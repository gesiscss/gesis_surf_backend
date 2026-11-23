"""
Tests for building the documents of the mobile events.
"""

from datetime import datetime, timezone
from typing import Any

from core.indexes.mobile_accessibility_index import (
    MobileAccessibilityAppIndex,
    MobileAccessibilityBrowserIndex,
)
from core.indexes.mobile_vpn_index import (
    MobileVpnAppIndex,
    MobileVpnBrowserIndex,
)
from django.test import SimpleTestCase
from mobile.capture import documents

RECEIVED_AT = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)

EVENT: dict[str, Any] = {
    "ts": "2026-10-27T13:32:21.602Z",
    "tsElapsedRealtimeNanos": 92235657541028,
    "event": "visible_text",
    "sessionId": "a-20261027-133210",
    "app": {"package": "com.a.app", "activity": "a.Main"},
    "visibleText": "hello",
    "charCount": 5,
}


def build(
    event: dict[str, Any], category: str | None = "news", **params: Any
) -> dict[str, Any]:
    """
    Build the document of an accessibility event with sample values.
    """
    upload_params: dict[str, Any] = {
        "user_id": "participant",
        "module": "accessibility",
        "client": {},
        "categories": {},
        "received_at": RECEIVED_AT,
    }
    upload_params.update(params)
    return documents.build_document(
        event, MobileAccessibilityAppIndex, category, documents.Upload(**upload_params)
    )


class ParseEventTests(SimpleTestCase):
    """
    Tests for reading an event from a request.
    """

    def test_object_and_raw_line_are_the_same_event(self) -> None:
        """
        Tests an event can be sent as an object or as its JSON line.
        """
        line = '{"ts":"t","event":"e","sessionId":"s","n":9007199254740993}'

        self.assertEqual(documents.parse_event(line)["n"], 9007199254740993)
        self.assertEqual(documents.parse_event(EVENT), EVENT)

    def test_unusable_events_are_refused(self) -> None:
        """
        Tests lines that are not an event with the needed keys raise an error.
        """
        for item in ("not json", "[1]", 5, None, {"event": "e", "ts": "t"}, {}):
            with self.subTest(item=item):
                with self.assertRaises(ValueError):
                    documents.parse_event(item)


class RoutingTests(SimpleTestCase):
    """
    Tests for the category and index of an event.
    """

    def test_category_comes_from_the_policy(self) -> None:
        """
        Tests known apps get the policy category and others are unknown.
        """
        categories = {"com.a.app": "news"}
        other = {**EVENT, "app": {"package": "com.b.app"}}
        no_app = {key: value for key, value in EVENT.items() if key != "app"}

        self.assertEqual(documents.get_category(EVENT, categories), "news")
        self.assertEqual(documents.get_category(other, categories), "unknown")
        self.assertIsNone(documents.get_category(no_app, categories))

    def test_browsers_have_their_own_index(self) -> None:
        """
        Tests only the browser category goes to the browser index.
        """
        for module, category, index_class in (
            ("accessibility", "browser", MobileAccessibilityBrowserIndex),
            ("accessibility", "news", MobileAccessibilityAppIndex),
            ("accessibility", None, MobileAccessibilityAppIndex),
            ("vpn", "browser", MobileVpnBrowserIndex),
            ("vpn", "unknown", MobileVpnAppIndex),
        ):
            with self.subTest(module=module, category=category):
                self.assertIs(documents.get_index_class(module, category), index_class)


class BuildDocumentTests(SimpleTestCase):
    """
    Tests for the document stored for an event.
    """

    def test_field_names(self) -> None:
        """
        Tests the event keys become the declared snake_case fields.
        """
        document = build(EVENT)

        self.assertEqual(document["visible_text"], "hello")
        self.assertEqual(document["char_count"], 5)
        self.assertEqual(document["ts_elapsed_realtime_nanos"], 92235657541028)
        self.assertEqual(document["session_id"], "a-20261027-133210")
        self.assertEqual(document["app_package"], "com.a.app")
        self.assertEqual(document["app_activity"], "a.Main")
        self.assertEqual(document["raw"], EVENT)

    def test_server_fields_cannot_be_set_by_the_event(self) -> None:
        """
        Tests values the server decides replace what the event says.
        """
        event = {**EVENT, "userId": "other", "appCategory": "browser", "module": "vpn"}

        document = build(event)

        self.assertEqual(document["user_id"], "participant")
        self.assertEqual(document["app_category"], "news")
        self.assertEqual(document["module"], "accessibility")
        self.assertEqual(document["received_at"], RECEIVED_AT.isoformat())

    def test_undeclared_keys_stay_in_raw_only(self) -> None:
        """
        Tests a new key of the app does not reach the strict mapping.
        """
        event = {**EVENT, "newKey": 1}

        document = build(event)

        self.assertNotIn("new_key", document)
        self.assertEqual(document["raw"]["newKey"], 1)

    def test_nested_keys_are_converted(self) -> None:
        """
        Tests the keys inside counter objects follow the same naming.
        """
        event = {**EVENT, "health": {"eventsPerMinute": 3}}

        self.assertEqual(build(event)["health"], {"events_per_minute": 3})

    def test_policy_of_the_event_wins_over_the_upload(self) -> None:
        """
        Tests the envelope only fills the policy the event does not carry.
        """
        client = {"policy_version": "upload", "policy_source": "backend"}
        event = {**EVENT, "privacyPolicyVersion": "event"}

        document = build(event, client=client)

        self.assertEqual(document["policy_version"], "event")
        self.assertEqual(document["policy_source"], "backend")

    def test_empty_values_are_not_stored(self) -> None:
        """
        Tests events without an app have no app fields.
        """
        event = {key: value for key, value in EVENT.items() if key != "app"}

        document = build(event, category=None)

        for name in ("app_package", "app_activity", "app_category"):
            self.assertNotIn(name, document)


class DocumentIdTests(SimpleTestCase):
    """
    Tests for the document id.
    """

    def test_same_event_same_id(self) -> None:
        """
        Tests an upload repeated gives the same id.
        """
        self.assertEqual(
            documents.document_id("participant", "vpn", EVENT),
            documents.document_id("participant", "vpn", dict(EVENT)),
        )

    def test_different_events_different_ids(self) -> None:
        """
        Tests the user, module and flow or marker change the id.
        """
        ids = {
            documents.document_id("participant", "vpn", EVENT),
            documents.document_id("other", "vpn", EVENT),
            documents.document_id("participant", "accessibility", EVENT),
            documents.document_id("participant", "vpn", {**EVENT, "flowId": "t-1"}),
            documents.document_id("participant", "vpn", {**EVENT, "markerId": "c-1"}),
        }

        self.assertEqual(len(ids), 5)
