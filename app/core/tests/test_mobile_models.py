"""
Tests for the mobile policy models.
"""

# pylint: disable=no-member

from typing import Any

from core import models
from core.tests.helpers import create_user
from django.db import IntegrityError, transaction
from rest_framework.test import APITestCase

HASH = "sha256:" + "a" * 64


def create_release(version: str, **params: Any) -> models.MobilePolicyRelease:
    """
    Create and return a sample mobile policy release.
    """
    defaults = {
        "policy_hash": HASH,
        "payload": {"schema_version": 1, "default_tier": "usage_only", "apps": []},
    }
    defaults.update(params)
    return models.MobilePolicyRelease.objects.create(version=version, **defaults)


class MobileAppModelTests(APITestCase):
    """
    Tests for the MobileApp model.
    """

    def test_defaults(self) -> None:
        """
        Tests an app is usage only, active and categorised as other by default.
        """
        app = models.MobileApp.objects.create(package_name="com.example.app")

        self.assertEqual(app.tier, "usage_only")
        self.assertEqual(app.category, "other")
        self.assertTrue(app.is_active)
        self.assertEqual(str(app), "com.example.app (usage_only)")

    def test_package_name_is_unique(self) -> None:
        """
        Tests two entries cannot share a package name.
        """
        models.MobileApp.objects.create(package_name="com.example.app")

        with self.assertRaises(IntegrityError), transaction.atomic():
            models.MobileApp.objects.create(package_name="com.example.app")

    def test_changes_are_recorded_in_history(self) -> None:
        """
        Tests a tier change leaves a history row (who/what/when audit trail).
        """
        app = models.MobileApp.objects.create(
            package_name="com.example.app", tier="usage_only"
        )
        app.tier = "tracked"
        app.save()

        self.assertEqual(app.history.count(), 2)  # type: ignore[attr-defined]
        self.assertEqual(app.history.first().tier, "tracked")  # type: ignore[attr-defined]


class MobilePolicyReleaseModelTests(APITestCase):
    """
    Tests for the MobilePolicyRelease model.
    """

    def test_only_one_release_can_be_active(self) -> None:
        """
        Tests a second active release is refused by the database.
        """
        create_release("2026.10.1", is_active=True)

        with self.assertRaises(IntegrityError), transaction.atomic():
            create_release("2026.10.2", is_active=True)

    def test_many_inactive_releases_are_allowed(self) -> None:
        """
        Tests old releases can be kept next to the active one.
        """
        create_release("2026.10.1")
        create_release("2026.10.2")
        create_release("2026.10.3", is_active=True)

        self.assertEqual(models.MobilePolicyRelease.objects.count(), 3)
        self.assertEqual(
            models.MobilePolicyRelease.objects.filter(is_active=True).count(), 1
        )

    def test_activation_can_move_to_another_release(self) -> None:
        """
        Tests rollback: deactivate the active release, then activate an old one.
        """
        old = create_release("2026.10.1")
        current = create_release("2026.10.2", is_active=True)

        current.is_active = False
        current.save()
        old.is_active = True
        old.save()

        self.assertEqual(
            models.MobilePolicyRelease.objects.get(is_active=True).version,
            "2026.10.1",
        )

    def test_payload_is_immutable(self) -> None:
        """
        Tests the payload of a stored release cannot be rewritten.
        """
        release = create_release("2026.10.1")
        release.payload = {"schema_version": 1, "default_tier": "tracked", "apps": []}

        with self.assertRaises(ValueError):
            release.save()

        release.refresh_from_db()
        self.assertEqual(release.payload["default_tier"], "usage_only")

    def test_hash_and_version_are_immutable(self) -> None:
        """
        Tests the hash and the version of a stored release cannot change.
        """
        release = create_release("2026.10.1")

        release.policy_hash = "sha256:" + "b" * 64
        with self.assertRaises(ValueError):
            release.save()

        release.refresh_from_db()
        release.version = "2026.10.9"
        with self.assertRaises(ValueError):
            release.save()

    def test_notes_can_change(self) -> None:
        """
        Tests the free-text notes stay editable.
        """
        release = create_release("2026.10.1")
        release.notes = "first pilot list"
        release.save()

        release.refresh_from_db()
        self.assertEqual(release.notes, "first pilot list")

    def test_created_by_is_kept_as_null_when_user_is_deleted(self) -> None:
        """
        Tests deleting the publisher does not delete the release.
        """
        user = create_user(user_id="publisher", password="test123")
        release = create_release("2026.10.1", created_by=user)

        user.delete()

        release.refresh_from_db()
        self.assertIsNone(release.created_by)


class MobileClientModelTests(APITestCase):
    """
    Tests for the MobileClient model.
    """

    def test_data_collection_defaults_to_true(self) -> None:
        """
        Tests a new mobile client collects data until it is switched off.
        """
        user = create_user(user_id="participant", password="test123")
        client = models.MobileClient.objects.create(user=user)

        self.assertTrue(client.data_collection)
        self.assertEqual(user.mobile_client, client)  # type: ignore[attr-defined]

    def test_one_client_per_user(self) -> None:
        """
        Tests a user cannot have two mobile clients.
        """
        user = create_user(user_id="participant", password="test123")
        models.MobileClient.objects.create(user=user)

        with self.assertRaises(IntegrityError), transaction.atomic():
            models.MobileClient.objects.create(user=user)

    def test_kill_switch_change_is_recorded_in_history(self) -> None:
        """
        Tests switching data collection off leaves an audit row.
        """
        user = create_user(user_id="participant", password="test123")
        client = models.MobileClient.objects.create(user=user)
        client.data_collection = False
        client.save()

        self.assertEqual(client.history.count(), 2)  # type: ignore[attr-defined]
        self.assertFalse(client.history.first().data_collection)  # type: ignore[attr-defined]
