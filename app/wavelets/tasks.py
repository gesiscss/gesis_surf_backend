"""
Bounded, owner-scoped repair of explicitly pending wavelet documents.
"""

import logging
from datetime import datetime
from time import monotonic
from typing import Any
from uuid import UUID

from celery import shared_task
from django.conf import settings
from django.db import DatabaseError
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from elasticsearch import ApiError, ConflictError, Elasticsearch, TransportError
from elasticsearch_dsl import connections
from redis import Redis
from redis.exceptions import RedisError
from redis.lock import Lock
from wavelets.linkage import resolve_domain_id
from wavelets.llm.serializers import INDEX_MAPPING as LLM_INDEX_MAPPING
from wavelets.social.serializers import INDEX_MAPPING as SOCIAL_INDEX_MAPPING

logger = logging.getLogger(__name__)

BATCH_SIZE = 500
RESOLUTION_WINDOW_SECONDS = 300
BATCH_TIME_SECONDS = 80
LOCK_SECONDS = 180
LOCK_KEY = "wavelets:resolve-pending:lock"


def _index_patterns() -> list[str]:
    indexes = set(LLM_INDEX_MAPPING.values())
    indexes.update(
        index
        for platform in SOCIAL_INDEX_MAPPING.values()
        for index in platform.values()
    )
    # pylint: disable=protected-access
    return sorted(f"{index._index._name}_*" for index in indexes)


def _pending_metadata(source: dict[str, Any]) -> tuple[UUID, str, datetime]:
    if (
        not isinstance(source["user_id"], str)
        or not isinstance(source["domain_session_id"], str)
        or not source["domain_session_id"].strip()
        or not isinstance(source["created_at"], str)
        or source.get("domain_id")
    ):
        raise ValueError("Invalid pending linkage metadata.")
    owner = UUID(source["user_id"])
    created_at = parse_datetime(source["created_at"])
    if created_at is None or timezone.is_naive(created_at):
        raise ValueError("Invalid pending creation time.")
    return owner, source["domain_session_id"], created_at


def _resolve_batch(client: Elasticsearch, lock: Lock, counts: dict[str, int]) -> None:
    started = monotonic()
    response = client.search(
        index=_index_patterns(),
        allow_no_indices=True,
        ignore_unavailable=True,
        allow_partial_search_results=False,
        query={"term": {"link_status": "pending"}},
        size=BATCH_SIZE,
        seq_no_primary_term=True,
        source=["user_id", "domain_session_id", "domain_id", "created_at"],
        sort=[
            {
                "updated_at": {
                    "order": "asc",
                    "missing": "_first",
                    "unmapped_type": "date",
                }
            },
        ],
    )
    if response.get("timed_out") or response["_shards"]["failed"]:
        raise RuntimeError(
            "Incomplete pending wavelet search; refusing partial repair."
        )

    for hit in response["hits"]["hits"]:
        if monotonic() - started >= BATCH_TIME_SECONDS:
            break
        counts["examined"] += 1
        now = timezone.now()
        changes: dict[str, Any] = {"updated_at": now.isoformat()}
        state = "pending"
        try:
            owner, hint, created_at = _pending_metadata(hit["_source"])
        except (KeyError, TypeError, ValueError):
            counts["malformed"] += 1
            logger.warning(
                "Malformed pending wavelet: index=%s id=%s", hit["_index"], hit["_id"]
            )
        else:
            domain_id, outcome = resolve_domain_id(owner, hint)
            if outcome == "matched":
                changes.update(domain_id=str(domain_id), link_status="linked")
                state = "linked"
            else:
                if outcome == "ambiguous":
                    counts["ambiguous"] += 1
                    logger.warning(
                        "Ambiguous pending wavelet: index=%s id=%s",
                        hit["_index"],
                        hit["_id"],
                    )
                if (now - created_at).total_seconds() >= RESOLUTION_WINDOW_SECONDS:
                    changes["link_status"] = "expired"
                    state = "expired"

        # Refresh the lease before writing; Redis verifies the ownership token.
        lock.extend(LOCK_SECONDS, replace_ttl=True)
        try:
            result = client.update(
                index=hit["_index"],
                id=hit["_id"],
                if_seq_no=hit["_seq_no"],
                if_primary_term=hit["_primary_term"],
                doc=changes,
            )
        except ConflictError:
            counts["conflicted"] += 1
            logger.info(
                "Pending wavelet changed concurrently: index=%s id=%s",
                hit["_index"],
                hit["_id"],
            )
            continue
        if result["result"] not in ("updated", "noop"):
            raise RuntimeError("Unexpected pending wavelet update result.")
        counts[state] += 1


@shared_task(bind=True, max_retries=3, soft_time_limit=100, time_limit=120)
def resolve_pending_wavelets(self) -> dict[str, Any]:
    """Process one repair batch; legacy documents are never selected."""
    counts = dict.fromkeys(
        (
            "examined",
            "linked",
            "pending",
            "expired",
            "ambiguous",
            "malformed",
            "conflicted",
            "failed",
        ),
        0,
    )
    try:
        with Redis.from_url(settings.CELERY_BROKER_URL) as redis:
            lock = redis.lock(
                LOCK_KEY, timeout=LOCK_SECONDS, blocking=False, thread_local=False
            )
            if not lock.acquire():
                logger.info(
                    "Skipping pending wavelet repair: another run holds the lock."
                )
                return {"status": "locked", **counts}
            try:
                client = connections.get_connection().options(
                    request_timeout=10, max_retries=0
                )
                _resolve_batch(client, lock, counts)
            finally:
                # Never remove a replacement worker's lock after losing our lease.
                if lock.owned():
                    lock.release()
                else:
                    logger.warning("Pending wavelet repair lock ownership was lost.")
    except (DatabaseError, ApiError, TransportError, RedisError) as error:
        counts["failed"] += 1
        logger.error(
            "Pending wavelet repair dependency failure: %s", type(error).__name__
        )
        raise self.retry(
            exc=error, countdown=min(60, 5 * 2**self.request.retries)
        ) from error
    except RuntimeError as error:
        counts["failed"] += 1
        logger.exception("Pending wavelet repair returned an incomplete result.")
        raise self.retry(
            exc=error, countdown=min(60, 5 * 2**self.request.retries)
        ) from error
    finally:
        logger.info("Pending wavelet repair counts: %s", counts)
    return {"status": "completed", **counts}
