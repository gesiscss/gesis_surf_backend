"""
Builds Elasticsearch documents from mobile app events.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from functools import cache
from typing import Any

from core.indexes.base_index import BaseIndex
from core.indexes.mobile_accessibility_index import (
    MobileAccessibilityAppIndex,
    MobileAccessibilityBrowserIndex,
)
from core.indexes.mobile_vpn_index import (
    MobileVpnAppIndex,
    MobileVpnBrowserIndex,
)

INGEST_SCHEMA_VERSION = 1

# (module, is browser) -> index class
INDEX_CLASSES: dict[tuple[str, bool], type[BaseIndex]] = {
    ("accessibility", False): MobileAccessibilityAppIndex,
    ("accessibility", True): MobileAccessibilityBrowserIndex,
    ("vpn", False): MobileVpnAppIndex,
    ("vpn", True): MobileVpnBrowserIndex,
}

REQUIRED_KEYS = ("event", "sessionId", "ts")

# Event keys that do not follow the plain camelCase to snake_case rule
FIELD_NAMES = {
    "sessionId": "session_id",
    "tsElapsedRealtimeNanos": "ts_elapsed_realtime_nanos",
    "prevTsElapsedRealtimeNanos": "prev_ts_elapsed_ns",
    "createdAt": "flow_created_at",
    "createdAtElapsedRealtimeNanos": "flow_created_at_elapsed_ns",
    "lastSeen": "flow_last_seen",
    "lastSeenElapsedRealtimeNanos": "flow_last_seen_elapsed_ns",
    "vpnMarkerElapsedRealtimeNanos": "vpn_marker_elapsed_ns",
    "accessibilityMarkerElapsedRealtimeNanos": "accessibility_marker_elapsed_ns",
    "privacyPolicyVersion": "policy_version",
    "privacyPolicyHash": "policy_hash",
    "privacyPolicySource": "policy_source",
}

# Set by the server or derived from the policy, never taken over from the event
IGNORED_KEYS = {"app", "appCategory", "module"}

# Values of the upload envelope used when the event does not carry its own
CLIENT_FIELDS = ("app_version", "policy_version", "policy_hash", "policy_source")


@dataclass(frozen=True)
class Upload:
    """
    What is known about an upload besides its events: who sent it, for which
    module, what the app reported, the categories of the active policy and
    when it arrived.
    """

    user_id: str
    module: str
    client: dict[str, str]
    categories: dict[str, str]
    received_at: datetime


def parse_event(item: Any) -> dict[str, Any]:
    """
    Return the event as a dict. The event may be sent as an object or as the
    raw JSON line. Raises ValueError if it cannot be used.
    """
    if isinstance(item, str):
        try:
            item = json.loads(item)
        except ValueError as error:
            raise ValueError("The line is not valid JSON.") from error

    if not isinstance(item, dict):
        raise ValueError("The event must be a JSON object.")

    for key in REQUIRED_KEYS:
        if not isinstance(item.get(key), str) or not item[key]:
            raise ValueError(f"The event needs a text value for {key!r}.")

    return item


def get_package(event: dict[str, Any]) -> str | None:
    """
    Return the package of the app the event belongs to, if any.
    """
    app = event.get("app")
    return app.get("package") if isinstance(app, dict) else None


def get_category(event: dict[str, Any], categories: dict[str, str]) -> str | None:
    """
    Return the category of the event's app from the policy. Apps that are not
    in the policy are "unknown"; events without an app have no category.
    """
    package = get_package(event)
    if package is None:
        return None
    return categories.get(package, "unknown")


def get_index_class(module: str, category: str | None) -> type[BaseIndex]:
    """
    Return the index class for a module and category: browsers have their own.
    """
    return INDEX_CLASSES[(module, category == "browser")]


def snake_case(key: str) -> str:
    """
    Return the Elasticsearch field name of an event key.
    """
    return FIELD_NAMES.get(key) or re.sub(r"[A-Z]", lambda m: f"_{m[0].lower()}", key)


def snake_keys(value: Any) -> Any:
    """
    Apply snake_case to the keys of a nested object.
    """
    if isinstance(value, dict):
        return {snake_case(key): snake_keys(item) for key, item in value.items()}
    return value


@cache
def declared_fields(index_class: type[BaseIndex]) -> frozenset[str]:
    """
    Return the field names declared on the index class.
    """
    # pylint: disable=protected-access
    mapping = index_class._doc_type.mapping.to_dict()
    return frozenset(mapping.get("properties", {}))


def build_document(
    event: dict[str, Any],
    index_class: type[BaseIndex],
    category: str | None,
    upload: Upload,
) -> dict[str, Any]:
    """
    Build the document stored for an event: the declared fields of the event,
    the server fields and the untouched event in "raw". Keys that the index
    does not declare are only kept in "raw".
    """
    document: dict[str, Any] = {
        snake_case(key): snake_keys(value)
        for key, value in event.items()
        if key not in IGNORED_KEYS
    }

    app = event.get("app")
    document.update(
        {
            "user_id": upload.user_id,
            "module": upload.module,
            "received_at": upload.received_at.isoformat(),
            "app_package": get_package(event),
            "app_activity": app.get("activity") if isinstance(app, dict) else None,
            "app_category": category,
            "ingest_schema_version": INGEST_SCHEMA_VERSION,
            "raw": event,
        }
    )
    for name in CLIENT_FIELDS:
        document.setdefault(name, upload.client.get(name))

    fields = declared_fields(index_class)
    return {
        name: value
        for name, value in document.items()
        if value is not None and name in fields
    }


def document_id(user_id: str, module: str, event: dict[str, Any]) -> str:
    """
    Return the document id of an event, the same every time it is uploaded.
    """
    parts = [
        user_id,
        module,
        event["sessionId"],
        event["event"],
        event["ts"],
        event.get("tsElapsedRealtimeNanos"),
        event.get("flowId") or event.get("markerId"),
    ]
    return hashlib.sha256("|".join(str(part) for part in parts).encode()).hexdigest()
