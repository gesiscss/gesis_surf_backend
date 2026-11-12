"""
Tests for the mobile policy API.
"""

# pylint: disable=no-member

from datetime import datetime, timezone
from typing import Any

from core.models import MobileClient, MobilePolicyRelease
from core.tests.helpers import create_user
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

POLICY_URL = reverse("policy:mobile-policy")

HASH = "sha256:" + "a" * 64
APPS = [
    {"package": "com.a.app", "tier": "tracked", "category": "news"},
    {"package": "com.b.app", "tier": "usage_only", "category": "email"},
]


def create_release(version: str = "2026.10.1", **params: Any) -> MobilePolicyRelease:
    """
    Create and return a sample mobile policy release.
    """
    defaults: dict[str, Any] = {
        "policy_hash": HASH,
        "payload": {"schema_version": 1, "default_tier": "usage_only", "apps": APPS},
    }
    defaults.update(params)
    return MobilePolicyRelease.objects.create(version=version, **defaults)


def client_for(user_id: str) -> tuple[APIClient, Any]:
    """
    Create a user and return an API client authenticated as that user.
    """
    user = create_user(user_id=user_id, password="test123")
    client = APIClient()
    client.force_authenticate(user)
    return client, user


class PublicMobilePolicyApiTests(TestCase):
    """
    Tests for the mobile policy API without authentication.
    """

    def test_auth_required(self) -> None:
        """
        Tests the policy is not served without a token.
        """
        create_release(is_active=True)

        response = APIClient().get(POLICY_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateMobilePolicyApiTests(TestCase):
    """
    Tests for the mobile policy API as an authenticated participant.
    """

    def setUp(self) -> None:
        self.client, self.user = client_for("participant")

    def test_returns_the_contract_shape(self) -> None:
        """
        Tests the response has exactly the keys the mobile app accepts.
        """
        release = create_release(is_active=True)

        response = self.client.get(POLICY_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(response.data),
            {
                "schema_version",
                "policy_version",
                "policy_hash",
                "issued_at",
                "data_collection",
                "default_tier",
                "apps",
            },
        )
        self.assertEqual(response.data["schema_version"], 1)
        self.assertEqual(response.data["policy_version"], "2026.10.1")
        self.assertEqual(response.data["policy_hash"], HASH)
        self.assertEqual(response.data["default_tier"], "usage_only")
        self.assertIs(response.data["data_collection"], True)
        self.assertEqual([dict(app) for app in response.data["apps"]], APPS)
        for app in response.data["apps"]:
            self.assertEqual(set(app), {"package", "tier", "category"})
        issued_at = datetime.strptime(response.data["issued_at"], "%Y-%m-%dT%H:%M:%SZ")
        self.assertEqual(
            issued_at.replace(tzinfo=timezone.utc),
            release.created_at.replace(microsecond=0),
        )

    def test_no_active_release_is_an_error(self) -> None:
        """
        Tests an empty or all-inactive release table is never served as a list.
        """
        create_release(is_active=False)

        response = self.client.get(POLICY_URL)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNotIn("apps", response.data)

    def test_serves_only_the_active_release(self) -> None:
        """
        Tests an old release is kept but never served.
        """
        create_release("2026.10.1")
        create_release("2026.10.2", is_active=True)

        response = self.client.get(POLICY_URL)

        self.assertEqual(response.data["policy_version"], "2026.10.2")

    def test_etag_round_trip(self) -> None:
        """
        Tests the same ETag answers 304 without a body.
        """
        create_release(is_active=True)
        etag = self.client.get(POLICY_URL)["ETag"]

        response = self.client.get(POLICY_URL, HTTP_IF_NONE_MATCH=etag)

        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)
        self.assertEqual(response["ETag"], etag)
        self.assertEqual(response.content, b"")

    def test_etag_matching_forms(self) -> None:
        """
        Tests weak, listed and wildcard If-None-Match values also match.
        """
        create_release(is_active=True)
        etag = self.client.get(POLICY_URL)["ETag"]

        for header in (f"W/{etag}", f'"other", {etag}', "*"):
            with self.subTest(header=header):
                response = self.client.get(POLICY_URL, HTTP_IF_NONE_MATCH=header)
                self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)

    def test_other_etag_gets_the_full_response(self) -> None:
        """
        Tests an unknown ETag is answered with the full policy.
        """
        create_release(is_active=True)

        response = self.client.get(POLICY_URL, HTTP_IF_NONE_MATCH='"other"')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_new_release_changes_the_etag(self) -> None:
        """
        Tests a newly published release is not hidden by a 304.
        """
        old = create_release(is_active=True)
        etag = self.client.get(POLICY_URL)["ETag"]
        old.is_active = False
        old.save()
        create_release("2026.10.2", policy_hash="sha256:" + "b" * 64, is_active=True)

        response = self.client.get(POLICY_URL, HTTP_IF_NONE_MATCH=etag)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["policy_version"], "2026.10.2")

    def test_kill_switch_is_not_hidden_by_a_304(self) -> None:
        """
        Tests switching data collection off changes the ETag for that user
        only, while the release hash stays the same.
        """
        create_release(is_active=True)
        etag = self.client.get(POLICY_URL)["ETag"]
        other_client, _ = client_for("other_participant")
        other_etag = other_client.get(POLICY_URL)["ETag"]

        MobileClient.objects.filter(user=self.user).update(data_collection=False)
        response = self.client.get(POLICY_URL, HTTP_IF_NONE_MATCH=etag)
        other_response = other_client.get(POLICY_URL, HTTP_IF_NONE_MATCH=other_etag)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(response.data["data_collection"], False)
        self.assertEqual(response.data["policy_hash"], HASH)
        self.assertNotEqual(response["ETag"], etag)
        self.assertEqual(other_response.status_code, status.HTTP_304_NOT_MODIFIED)

    def test_mobile_client_is_created_on_first_fetch(self) -> None:
        """
        Tests the per-user state appears lazily, collecting by default.
        """
        create_release(is_active=True)
        self.assertFalse(MobileClient.objects.filter(user=self.user).exists())

        self.client.get(POLICY_URL)

        self.assertTrue(MobileClient.objects.get(user=self.user).data_collection)

    def test_telemetry_is_stored_but_changes_nothing(self) -> None:
        """
        Tests the reported values are saved, trimmed to the field sizes, and
        the response is the same with or without them.
        """
        create_release(is_active=True)
        plain = self.client.get(POLICY_URL).data

        response = self.client.get(
            POLICY_URL,
            {
                "app_version": "1.0.0",
                "platform": "android",
                "policy_version": "bundled-1",
                "policy_source": "x" * 50,
            },
        )

        stored = MobileClient.objects.get(user=self.user)
        self.assertEqual(stored.app_version, "1.0.0")
        self.assertEqual(stored.platform, "android")
        self.assertEqual(stored.last_policy_version, "bundled-1")
        self.assertEqual(stored.last_policy_source, "x" * 16)
        self.assertIsNotNone(stored.last_seen_at)
        self.assertEqual(response.data, plain)

    def test_polling_does_not_add_history_rows(self) -> None:
        """
        Tests telemetry updates leave the history for real changes only.
        """
        create_release(is_active=True)

        for _ in range(3):
            self.client.get(POLICY_URL, {"app_version": "1.0.0"})

        self.assertEqual(MobileClient.objects.get(user=self.user).history.count(), 1)

    def test_openapi_schema_lists_the_endpoint(self) -> None:
        """
        Tests the endpoint is documented.
        """
        response = self.client.get("/api/schema/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"/api/mobile/policy/", response.content)
