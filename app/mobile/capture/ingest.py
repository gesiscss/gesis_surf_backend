"""
Writes mobile app events to Elasticsearch.
"""

from datetime import datetime, timezone
from typing import Any, cast

from core.indexes.base_index import BaseIndex
from elasticsearch import BadRequestError
from elasticsearch.helpers import bulk
from elasticsearch_dsl import connections
from mobile.capture import documents

HTTP_CONFLICT = 409


def ensure_index(index_class: type[BaseIndex]) -> None:
    """
    Create the index of the current month if it does not exist. A bulk write
    would otherwise create it with a default mapping.
    """
    try:
        index_class.create_current_month_index()
    except BadRequestError as error:
        if "resource_already_exists_exception" not in str(error):
            raise


def build_actions(
    upload: documents.Upload, items: list[Any]
) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, Any]]]:
    """
    Return the bulk actions for the usable events, the position in the request
    of each action by document id, and the errors of the unusable events.
    """
    actions: list[dict[str, Any]] = []
    positions: dict[str, int] = {}
    errors: list[dict[str, Any]] = []
    ensured = set()

    for position, item in enumerate(items):
        try:
            event = documents.parse_event(item)
        except ValueError as error:
            errors.append({"index": position, "detail": str(error)})
            continue

        category = documents.get_category(event, upload.categories)
        index_class = documents.get_index_class(upload.module, category)
        if index_class not in ensured:
            ensure_index(index_class)
            ensured.add(index_class)

        doc_id = documents.document_id(upload.user_id, upload.module, event)
        positions[doc_id] = position
        actions.append(
            {
                "_op_type": "create",
                "_index": index_class.get_current_index(),
                "_id": doc_id,
                "_source": documents.build_document(
                    event, index_class, category, upload
                ),
            }
        )

    return actions, positions, errors


def ingest_events(
    user_id: str,
    module: str,
    items: list[Any],
    client: dict[str, str],
    categories: dict[str, str],
) -> dict[str, Any]:
    """
    Store the events and return how many were accepted, were already stored
    (duplicates) or were rejected. Every item is counted exactly once and
    errors carry the position of the item in the request.
    """
    upload = documents.Upload(
        user_id, module, client, categories, datetime.now(timezone.utc)
    )
    actions, positions, errors = build_actions(upload, items)

    accepted, failures = bulk(
        connections.get_connection(), actions, raise_on_error=False, stats_only=False
    )

    duplicates = 0
    for failure in cast(list[dict[str, Any]], failures):
        result = failure["create"]
        if result["status"] == HTTP_CONFLICT:
            duplicates += 1
        else:
            reason = result.get("error", {}).get("reason", "The event was refused.")
            errors.append({"index": positions[result["_id"]], "detail": reason})

    errors.sort(key=lambda error: error["index"])
    return {
        "accepted": accepted,
        "duplicates": duplicates,
        "rejected": len(errors),
        "errors": errors,
    }
