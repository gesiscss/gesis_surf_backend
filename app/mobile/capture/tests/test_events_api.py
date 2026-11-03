"""
Tests for the mobile events API.
"""

# pylint: disable=no-member

import json
from typing import Any
from unittest.mock import patch

from core.indexes.base_index import BaseIndex
from core.indexes.mobile_accessibility_index import (
    MobileAccessibilityAppIndex,
    MobileAccessibilityBrowserIndex,
)
from core.indexes.mobile_vpn_index import (
    MobileVpnAppIndex,
    MobileVpnBrowserIndex,
)
from core.models import MobileClient, MobilePolicyRelease
from core.tests.helpers import create_user
from django.test import TestCase, override_settings
from django.urls import reverse
from elasticsearch.exceptions import TransportError
from elasticsearch_dsl import connections
from mobile.capture import serializers
from rest_framework import status
from rest_framework.test import APIClient

EVENTS_URL = reverse("capture:mobile-events")

TEST_INDEXES: dict[type[BaseIndex], str] = {
    MobileAccessibilityAppIndex: "test_mobile_accessibility_app",
    MobileAccessibilityBrowserIndex: "test_mobile_accessibility_browser",
    MobileVpnAppIndex: "test_mobile_vpn_app",
    MobileVpnBrowserIndex: "test_mobile_vpn_browser",
}

APPS = [
    {"package": "com.news.app", "tier": "tracked", "category": "news"},
    {"package": "com.browser.app", "tier": "tracked", "category": "browser"},
]
CLIENT = {
    "app_version": "1.0.0",
    "policy_version": "2026.10.1",
    "policy_hash": "sha256:" + "a" * 64,
    "policy_source": "backend",
}


def create_event(package: str | None = "com.news.app", **params: Any) -> dict[str, Any]:
    """
    Create and return a sample accessibility event.
    """
    event: dict[str, Any] = {
        "ts": "2026-10-27T13:32:21.602Z",
        "tsElapsedRealtimeNanos": 92235657541028,
        "event": "visible_text",
        "sessionId": "a-20261027-133210",
        "visibleText": "hello world",
        "charCount": 11,
    }
    if package:
        event["app"] = {"package": package, "activity": "a.Main"}
    event.update(params)
    return event


class MobileEventsTestCase(TestCase):
    """
    Base for the mobile events API tests. Events are written to throwaway
    indexes, never to the monthly ones.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(user_id="participant", password="test123")
        self.client.force_authenticate(self.user)
        MobilePolicyRelease.objects.create(
            version="2026.10.1",
            policy_hash=CLIENT["policy_hash"],
            payload={"schema_version": 1, "default_tier": "usage_only", "apps": APPS},
            is_active=True,
        )

        self.es_client = connections.get_connection()
        for index_class, name in TEST_INDEXES.items():
            patcher = patch.object(index_class, "get_current_index", return_value=name)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.delete_indexes()
        self.addCleanup(self.delete_indexes)

    def delete_indexes(self) -> None:
        """
        Delete the throwaway indexes.
        """
        self.es_client.indices.delete(
            index=list(TEST_INDEXES.values()), ignore_unavailable=True
        )

    def post(self, events: list[Any], **body: Any) -> Any:
        """
        Upload accessibility events with a sample envelope.
        """
        payload = {"module": "accessibility", "events": events, "client": CLIENT}
        payload.update(body)
        return self.client.post(EVENTS_URL, payload, format="json")

    def stored(self, index_class: type[BaseIndex]) -> list[dict[str, Any]]:
        """
        Return the documents stored in the throwaway index of the class.
        """
        name = TEST_INDEXES[index_class]
        self.es_client.indices.refresh(index=name, ignore_unavailable=True)
        found = self.es_client.search(index=name, size=100, ignore_unavailable=True)
        return [hit["_source"] for hit in found["hits"]["hits"]]


class StoreMobileEventsTests(MobileEventsTestCase):
    """
    Tests for the events that are stored.
    """

    def test_events_are_stored_with_server_fields(self) -> None:
        """
        Tests the user, category and policy are set by the server and the
        event is kept as sent.
        """
        event = create_event(userId="other", appCategory="browser")

        response = self.post([event])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data,
            {"accepted": 1, "duplicates": 0, "rejected": 0, "errors": []},
        )
        (document,) = self.stored(MobileAccessibilityAppIndex)
        self.assertEqual(document["user_id"], "participant")
        self.assertEqual(document["app_category"], "news")
        self.assertEqual(document["visible_text"], "hello world")
        self.assertEqual(document["policy_version"], "2026.10.1")
        self.assertEqual(document["policy_source"], "backend")
        self.assertEqual(document["raw"], event)
        self.assertEqual(self.stored(MobileAccessibilityBrowserIndex), [])

    def test_events_are_routed_by_module_and_category(self) -> None:
        """
        Tests browsers go to their own index and unknown apps to the app index.
        """
        events = [
            create_event("com.browser.app"),
            create_event("com.other.app", ts="2026-10-27T13:32:22.000Z"),
            create_event(None, event="accessibility_session_start"),
        ]

        response = self.post(events)
        vpn_response = self.post(
            [create_event("com.browser.app", event="tls_sni")], module="vpn"
        )

        self.assertEqual(response.data["accepted"], 3)
        self.assertEqual(vpn_response.data["accepted"], 1)
        (browser,) = self.stored(MobileAccessibilityBrowserIndex)
        self.assertEqual(browser["app_package"], "com.browser.app")
        categories = {
            document.get("app_category")
            for document in self.stored(MobileAccessibilityAppIndex)
        }
        self.assertEqual(categories, {"unknown", None})
        self.assertEqual(len(self.stored(MobileVpnBrowserIndex)), 1)
        self.assertEqual(self.stored(MobileVpnAppIndex), [])

    def test_missing_index_is_created_with_the_mapping(self) -> None:
        """
        Tests the first upload of a month creates the index with the class
        mapping instead of a default one.
        """
        self.post([create_event()])

        mapping = self.es_client.indices.get_mapping(
            index=TEST_INDEXES[MobileAccessibilityAppIndex]
        )

        mappings = mapping[TEST_INDEXES[MobileAccessibilityAppIndex]]["mappings"]
        self.assertEqual(mappings["dynamic"], "strict")

    def test_repeated_upload_is_all_duplicates(self) -> None:
        """
        Tests sending the same events again stores nothing new.
        """
        events = [create_event(), create_event(ts="2026-10-27T13:32:22.000Z")]
        self.post(events)

        response = self.post(events)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["accepted"], 0)
        self.assertEqual(response.data["duplicates"], 2)
        self.assertEqual(len(self.stored(MobileAccessibilityAppIndex)), 2)

    def test_every_event_is_counted_with_its_position(self) -> None:
        """
        Tests unusable events are rejected one by one, and the counts always
        add up to the events sent.
        """
        events = [create_event(), "not json", {"event": 1}, 5]

        response = self.post(events)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["accepted"], 1)
        self.assertEqual(response.data["rejected"], 3)
        self.assertEqual(
            [error["index"] for error in response.data["errors"]], [1, 2, 3]
        )
        self.assertEqual(
            response.data["accepted"]
            + response.data["duplicates"]
            + response.data["rejected"],
            len(events),
        )

    def test_value_refused_by_elasticsearch_is_rejected(self) -> None:
        """
        Tests an event whose value does not fit its field is rejected with its
        position, while the others are stored.
        """
        events = [create_event(), create_event(ts="not a date")]

        response = self.post(events)

        self.assertEqual(response.data["accepted"], 1)
        self.assertEqual(response.data["rejected"], 1)
        self.assertEqual(response.data["errors"][0]["index"], 1)

    def test_nothing_stored_is_a_bad_request(self) -> None:
        """
        Tests a request in which every event is rejected is answered with 400.
        """
        response = self.post(["not json"])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["rejected"], 1)

    def test_large_numbers_stay_exact(self) -> None:
        """
        Tests a value above the safe integer range of JavaScript is stored
        as sent, whether the event is an object or a raw line.
        """
        value = 2**62 + 1
        line = json.dumps(create_event(ts="2026-10-27T13:32:22.000Z"))
        line = line.replace("92235657541028", str(value))

        self.post([create_event(tsElapsedRealtimeNanos=value), line])

        values = {
            document["ts_elapsed_realtime_nanos"]
            for document in self.stored(MobileAccessibilityAppIndex)
        }
        self.assertEqual(values, {value})

    def test_new_key_of_the_app_does_not_fail_the_upload(self) -> None:
        """
        Tests a key without a field is kept in raw and nothing is rejected.
        """
        response = self.post([create_event(newKey={"a": 1})])

        self.assertEqual(response.data["accepted"], 1)
        (document,) = self.stored(MobileAccessibilityAppIndex)
        self.assertEqual(document["raw"]["newKey"], {"a": 1})
        self.assertNotIn("new_key", document)

    def test_policy_of_the_event_wins_over_the_upload(self) -> None:
        """
        Tests the policy in the event is kept, the others get the upload's.
        """
        start = create_event(
            None, event="accessibility_session_start", privacyPolicyVersion="2026.9.9"
        )

        self.post([start, create_event()])

        versions = {
            document["event"]: document["policy_version"]
            for document in self.stored(MobileAccessibilityAppIndex)
        }
        self.assertEqual(
            versions,
            {"accessibility_session_start": "2026.9.9", "visible_text": "2026.10.1"},
        )


class RefuseMobileEventsTests(MobileEventsTestCase):
    """
    Tests for the uploads that are refused or must be retried.
    """

    def test_auth_required(self) -> None:
        """
        Tests events are not accepted without a token.
        """
        response = APIClient().post(EVENTS_URL, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_data_collection_switched_off(self) -> None:
        """
        Tests a user with data collection switched off cannot upload.
        """
        MobileClient.objects.create(user=self.user, data_collection=False)

        response = self.post([create_event()])

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.stored(MobileAccessibilityAppIndex), [])

    def test_invalid_envelope(self) -> None:
        """
        Tests a wrong module, no events or too many events are refused.
        """
        events = [create_event()]
        cases: list[tuple[str, list[Any]]] = [
            ("other", events),
            ("vpn", []),
            ("vpn", events * (serializers.MAX_EVENTS + 1)),
        ]

        for module, sent in cases:
            with self.subTest(module=module, events=len(sent)):
                response = self.post(sent, module=module)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_active_release_is_a_retry(self) -> None:
        """
        Tests events are not stored without a policy to take the categories
        from, and the app is told to try again.
        """
        MobilePolicyRelease.objects.update(is_active=False)

        response = self.post([create_event()])

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_storage_failure_is_a_retry(self) -> None:
        """
        Tests an unavailable Elasticsearch is answered with 503.
        """
        with patch(
            "mobile.capture.views.ingest.ingest_events",
            side_effect=TransportError("down"),
        ):
            response = self.post([create_event()])

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @override_settings(MAINTENANCE_MODE=True)
    def test_maintenance_mode(self) -> None:
        """
        Tests uploads are paused in maintenance mode.
        """
        response = self.post([create_event()])

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_openapi_schema_lists_the_endpoint(self) -> None:
        """
        Tests the endpoint is documented.
        """
        response = self.client.get("/api/schema/")

        self.assertIn(b"/api/mobile/events/", response.content)
