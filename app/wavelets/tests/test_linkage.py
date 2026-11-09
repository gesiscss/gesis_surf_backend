"""
Regression tests for bounded wavelet resolution and task orchestration.
"""

from datetime import timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

from celery.exceptions import Retry
from core.tests.helpers import create_domain, create_user
from django.conf import settings
from django.db import DatabaseError
from django.test import TestCase
from django.utils import timezone
from elastic_transport import ApiResponseMeta, NodeConfig
from elasticsearch import ApiError, ConflictError
from elasticsearch_dsl import connections
from redis import Redis
from redis.exceptions import LockError, LockNotOwnedError
from wavelets.linkage import resolve_domain_id
from wavelets.tasks import LOCK_SECONDS, _index_patterns, resolve_pending_wavelets


class ResolverTests(TestCase):
    def setUp(self):
        self.user = create_user(user_id="linkage-owner")
        self.hint = "global-session-example-windowId-1-tabId-2-domain-host-visit-time"

    def test_exact_owned_match(self):
        domain = create_domain(user=self.user, domain_session_id=self.hint)
        self.assertEqual(
            resolve_domain_id(self.user.pk, self.hint), (domain.pk, "matched")
        )

    def test_other_participants_match_is_not_returned(self):
        other = create_user(user_id="linkage-other")
        create_domain(user=other, domain_session_id=self.hint)
        self.assertEqual(resolve_domain_id(self.user.pk, self.hint), (None, "missing"))

    def test_similar_hint_is_not_a_match(self):
        create_domain(user=self.user, domain_session_id=f"{self.hint}-different")
        self.assertEqual(resolve_domain_id(self.user.pk, self.hint), (None, "missing"))

    def test_repeated_hint_is_ambiguous(self):
        create_domain(user=self.user, domain_session_id=self.hint)
        create_domain(
            user=self.user,
            domain_session_id=self.hint,
            start_time=timezone.now() - timedelta(seconds=1),
        )
        self.assertEqual(
            resolve_domain_id(self.user.pk, self.hint), (None, "ambiguous")
        )


class RepairTaskTests(TestCase):
    def setUp(self):
        self.user = create_user(user_id="repair-owner")
        self.redis_patch = patch("wavelets.tasks.Redis.from_url")
        self.redis = self.redis_patch.start().return_value.__enter__.return_value
        self.addCleanup(self.redis_patch.stop)
        self.lock = self.redis.lock.return_value
        self.lock.acquire.return_value = True
        self.lock.owned.return_value = True
        self.connection_patch = patch("wavelets.tasks.connections.get_connection")
        self.client = self.connection_patch.start().return_value.options.return_value
        self.addCleanup(self.connection_patch.stop)
        self.client.update.return_value = {"result": "updated"}
        self.hit = {
            "_index": "chatgpt_index_2026_10",
            "_id": "test-document",
            "_seq_no": 3,
            "_primary_term": 1,
            "_source": {
                "user_id": str(self.user.pk),
                "domain_session_id": "scope-windowId-1-tabId-2-domain-host-visit-time",
                "created_at": timezone.now().isoformat(),
            },
        }
        self.set_hits(self.hit)

    def set_hits(self, *hits):
        self.client.search.return_value = {
            "hits": {"hits": list(hits)},
            "timed_out": False,
            "_shards": {"failed": 0},
        }

    def run_task(self):
        return resolve_pending_wavelets.run()

    def test_missing_stays_pending_then_domain_arrives(self):
        self.assertEqual(self.run_task()["pending"], 1)
        domain = create_domain(
            user=self.user,
            domain_session_id=self.hit["_source"]["domain_session_id"],
        )
        result = self.run_task()
        self.assertEqual(result["linked"], 1)
        call = self.client.update.call_args.kwargs
        self.assertEqual(call["doc"]["domain_id"], str(domain.pk))
        self.assertEqual(call["doc"]["link_status"], "linked")
        self.assertEqual(call["index"], self.hit["_index"])
        self.assertEqual(call["if_seq_no"], 3)
        self.assertEqual(call["if_primary_term"], 1)

    def test_final_lookup_links_even_after_deadline(self):
        self.hit["_source"]["created_at"] = (
            timezone.now() - timedelta(days=2)
        ).isoformat()
        create_domain(
            user=self.user,
            domain_session_id=self.hit["_source"]["domain_session_id"],
        )
        self.assertEqual(self.run_task()["linked"], 1)

    def test_missing_expires_after_window(self):
        self.hit["_source"]["created_at"] = (
            timezone.now() - timedelta(minutes=6)
        ).isoformat()
        self.assertEqual(self.run_task()["expired"], 1)
        self.assertEqual(
            self.client.update.call_args.kwargs["doc"]["link_status"], "expired"
        )

    def test_ambiguity_is_reported_without_guessing(self):
        hint = self.hit["_source"]["domain_session_id"]
        create_domain(user=self.user, domain_session_id=hint)
        create_domain(
            user=self.user,
            domain_session_id=hint,
            start_time=timezone.now() - timedelta(seconds=1),
        )
        with self.assertLogs("wavelets.tasks", level="WARNING"):
            result = self.run_task()
        self.assertEqual(result["ambiguous"], 1)
        self.assertEqual(result["pending"], 1)
        self.assertNotIn("domain_id", self.client.update.call_args.kwargs["doc"])

    def test_malformed_record_does_not_block_healthy_record(self):
        malformed = {**self.hit, "_id": "malformed", "_source": {}}
        self.set_hits(malformed, self.hit)
        with self.assertLogs("wavelets.tasks", level="WARNING"):
            result = self.run_task()
        self.assertEqual(result["malformed"], 1)
        self.assertEqual(result["examined"], 2)
        self.assertEqual(self.client.update.call_count, 2)

    def test_existing_domain_id_is_not_overwritten(self):
        self.hit["_source"]["domain_id"] = str(uuid4())
        with self.assertLogs("wavelets.tasks", level="WARNING"):
            result = self.run_task()
        self.assertEqual(result["malformed"], 1)
        self.assertNotIn("domain_id", self.client.update.call_args.kwargs["doc"])

    def test_lock_contention_skips_search(self):
        self.lock.acquire.return_value = False
        self.assertEqual(self.run_task()["status"], "locked")
        self.client.search.assert_not_called()
        self.lock.release.assert_not_called()

    def test_lease_is_renewed_and_released_by_owner(self):
        self.run_task()
        self.lock.extend.assert_called_once_with(LOCK_SECONDS, replace_ttl=True)
        self.lock.release.assert_called_once()

    def test_lost_lease_prevents_write_and_does_not_release_replacement(self):
        self.lock.extend.side_effect = LockNotOwnedError("Lost lock")
        self.lock.owned.return_value = False
        with patch.object(resolve_pending_wavelets, "retry", side_effect=Retry):
            with self.assertRaises(Retry):
                self.run_task()
        self.client.update.assert_not_called()
        self.lock.release.assert_not_called()

    def test_database_failure_retries_without_expiring(self):
        self.hit["_source"]["created_at"] = (
            timezone.now() - timedelta(days=2)
        ).isoformat()
        with (
            patch("wavelets.tasks.resolve_domain_id", side_effect=DatabaseError),
            patch.object(resolve_pending_wavelets, "retry", side_effect=Retry),
        ):
            with self.assertRaises(Retry):
                self.run_task()
        self.client.update.assert_not_called()
        self.lock.release.assert_called_once()

    def test_update_failure_retries_and_releases_lock(self):
        meta = ApiResponseMeta(
            status=503,
            http_version="1.1",
            headers={},
            duration=0,
            node=NodeConfig("http", "localhost", 9200),
        )
        self.client.update.side_effect = ApiError("unavailable", meta, {})
        with patch.object(resolve_pending_wavelets, "retry", side_effect=Retry):
            with self.assertRaises(Retry):
                self.run_task()
        self.lock.release.assert_called_once()

    def test_version_conflict_does_not_retry_over_existing_relationship(self):
        meta = ApiResponseMeta(
            status=409,
            http_version="1.1",
            headers={},
            duration=0,
            node=NodeConfig("http", "localhost", 9200),
        )
        self.client.update.side_effect = ConflictError("conflict", meta, {})
        self.assertEqual(self.run_task()["conflicted"], 1)
        self.assertEqual(self.client.update.call_count, 1)

    def test_partial_search_fails_without_writes(self):
        self.client.search.return_value["timed_out"] = True
        with patch.object(resolve_pending_wavelets, "retry", side_effect=Retry):
            with self.assertRaises(Retry):
                self.run_task()
        self.client.update.assert_not_called()
        self.lock.release.assert_called_once()

    def test_expired_ambiguity_is_not_linked_arbitrarily(self):
        hint = self.hit["_source"]["domain_session_id"]
        create_domain(user=self.user, domain_session_id=hint)
        create_domain(
            user=self.user,
            domain_session_id=hint,
            start_time=timezone.now() - timedelta(seconds=1),
        )
        self.hit["_source"]["created_at"] = (
            timezone.now() - timedelta(minutes=6)
        ).isoformat()
        with self.assertLogs("wavelets.tasks", level="WARNING"):
            result = self.run_task()
        self.assertEqual(result["ambiguous"], 1)
        self.assertEqual(result["expired"], 1)
        self.assertNotIn("domain_id", self.client.update.call_args.kwargs["doc"])

    def test_time_budget_stops_work_before_task_deadline(self):
        with patch("wavelets.tasks.monotonic", side_effect=[0, 81]):
            self.assertEqual(self.run_task()["examined"], 0)
        self.client.update.assert_not_called()
        self.lock.release.assert_called_once()

    def test_selection_is_pending_only_and_rotates_oldest_checked_first(self):
        self.run_task()
        query = self.client.search.call_args.kwargs
        self.assertEqual(query["query"], {"term": {"link_status": "pending"}})
        self.assertEqual(query["size"], 500)
        self.assertTrue(query["seq_no_primary_term"])
        self.assertEqual(query["sort"][0]["updated_at"]["order"], "asc")
        self.assertIn("updated_at", self.client.update.call_args.kwargs["doc"])
        self.assertTrue(all(pattern.endswith("_*") for pattern in _index_patterns()))
        self.assertIn("facebook_reels_index_*", _index_patterns())

    def test_schedule_is_disabled_by_default(self):
        self.assertFalse(settings.WAVELET_LINKAGE_ENABLED)
        self.assertNotIn("resolve-pending-wavelets", settings.CELERY_BEAT_SCHEDULE)


class RepairIntegrationTests(TestCase):
    """Use isolated indices and locks against the existing test services."""

    def setUp(self):
        self.user = create_user(user_id="integration-linkage")
        self.client = connections.get_connection()
        self.index = f"chatgpt_index_linkage_test_{uuid4().hex}"
        self.client.indices.create(
            index=self.index,
            mappings={
                "properties": {
                    "link_status": {"type": "keyword"},
                    "user_id": {"type": "keyword"},
                    "domain_session_id": {"type": "keyword"},
                    "domain_id": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                }
            },
        )
        self.addCleanup(self.client.indices.delete, index=self.index)
        self.pattern_patch = patch(
            "wavelets.tasks._index_patterns", return_value=[self.index]
        )
        self.pattern_patch.start()
        self.addCleanup(self.pattern_patch.stop)
        lock_patch = patch("wavelets.tasks.LOCK_KEY", f"wavelets:test:{uuid4().hex}")
        lock_patch.start()
        self.addCleanup(lock_patch.stop)

    def write(self, doc_id, **fields):
        source = {
            "user_id": str(self.user.pk),
            "domain_session_id": "scope-windowId-1-tabId-2-domain-host-visit-time",
            "created_at": timezone.now().isoformat(),
            "updated_at": timezone.now().isoformat(),
            "link_status": "pending",
        }
        source.update(fields)
        self.client.index(index=self.index, id=doc_id, document=source, refresh=True)
        return source

    def test_late_arrival_links_and_legacy_stays_untouched(self):
        source = self.write("pending")
        legacy = {"domain_id": "", "message_content": "historical document"}
        self.client.index(index=self.index, id="legacy", document=legacy, refresh=True)
        first = resolve_pending_wavelets.run()
        self.assertEqual(first["pending"], 1)
        domain = create_domain(
            user=self.user, domain_session_id=source["domain_session_id"]
        )
        self.client.indices.refresh(index=self.index)
        self.assertEqual(resolve_pending_wavelets.run()["linked"], 1)
        stored = self.client.get(index=self.index, id="pending")["_source"]
        self.assertEqual(stored["domain_id"], str(domain.pk))
        self.assertEqual(stored["link_status"], "linked")
        self.assertEqual(
            self.client.get(index=self.index, id="legacy")["_source"], legacy
        )
        self.client.indices.refresh(index=self.index)
        self.assertEqual(resolve_pending_wavelets.run()["examined"], 0)

    def test_concurrent_link_is_not_overwritten(self):
        self.write("pending")
        concurrent_id = str(uuid4())

        def link_concurrently(owner, hint):
            self.client.update(
                index=self.index,
                id="pending",
                doc={"domain_id": concurrent_id, "link_status": "linked"},
            )
            return uuid4(), "matched"

        with patch("wavelets.tasks.resolve_domain_id", side_effect=link_concurrently):
            result = resolve_pending_wavelets.run()
        self.assertEqual(result["conflicted"], 1)
        stored = self.client.get(index=self.index, id="pending")["_source"]
        self.assertEqual(stored["domain_id"], concurrent_id)

    def test_bounded_batches_rotate_including_malformed_documents(self):
        self.write("first", user_id="invalid-uuid")
        self.write("second")
        self.write("third", created_at=(timezone.now() - timedelta(days=2)).isoformat())
        with patch("wavelets.tasks.BATCH_SIZE", 1):
            results = []
            for _ in range(3):
                results.append(resolve_pending_wavelets.run())
                self.client.indices.refresh(index=self.index)
        self.assertEqual(sum(result["examined"] for result in results), 3)
        self.assertEqual(sum(result["malformed"] for result in results), 1)
        self.assertEqual(sum(result["expired"] for result in results), 1)

    def test_real_redis_lock_release_preserves_new_owner(self):
        with Redis.from_url(settings.CELERY_BROKER_URL) as redis:
            key = f"wavelets:test:{uuid4().hex}"
            first = redis.lock(key, timeout=30, thread_local=False)
            second = redis.lock(key, timeout=30, thread_local=False)
            self.assertTrue(first.acquire(blocking=False))
            self.assertFalse(second.acquire(blocking=False))
            first.release()
            self.assertTrue(second.acquire(blocking=False))
            try:
                with self.assertRaises(LockError):
                    first.extend(30)
                self.assertFalse(first.owned())
                self.assertTrue(second.owned())
            finally:
                second.release()
