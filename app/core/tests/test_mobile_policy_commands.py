"""
Tests for the mobile policy helpers and the seed and publish commands.
"""

# pylint: disable=no-member

from io import StringIO
from typing import Any

from core.management.commands.seed_mobile_policy import MOBILE_APPS
from core.mobile_policy import (
    build_payload,
    canonical_json,
    compute_policy_hash,
    validate_payload,
)
from core.models import MobileApp, MobilePolicyRelease
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


def run(command: str, *args: str) -> str:
    """
    Run a management command and return what it printed.
    """
    out = StringIO()
    call_command(command, *args, stdout=out)
    return out.getvalue()


def create_app(package: str, **params: Any) -> MobileApp:
    """
    Create and return a sample allow-list entry.
    """
    return MobileApp.objects.create(package_name=package, **params)


class MobilePolicyHelperTests(TestCase):
    """
    Tests for the canonical payload and the hash.
    """

    def test_canonical_json_is_compact_and_sorted(self) -> None:
        """
        Tests the text the hash is built from does not change by accident.
        """
        payload = build_payload(
            [{"package": "com.b.app", "tier": "tracked", "category": "news"}]
        )

        self.assertEqual(
            canonical_json(payload),
            '{"apps":[{"category":"news","package":"com.b.app","tier":"tracked"}],'
            '"default_tier":"usage_only","schema_version":1}',
        )

    def test_hash_does_not_depend_on_input_order(self) -> None:
        """
        Tests the same allow-list gives the same hash in any order.
        """
        one = {"package": "com.a.app", "tier": "tracked", "category": "news"}
        two = {"package": "com.b.app", "tier": "usage_only", "category": "email"}

        hash_ab = compute_policy_hash(build_payload([one, two]))
        hash_ba = compute_policy_hash(build_payload([two, one]))

        self.assertEqual(hash_ab, hash_ba)
        self.assertRegex(hash_ab, r"^sha256:[0-9a-f]{64}$")

    def test_seed_list_is_valid(self) -> None:
        """
        Tests the seeded list passes the same checks as a publish.
        """
        payload = build_payload(
            [
                {"package": package, "tier": tier, "category": category}
                for package, tier, category in MOBILE_APPS
            ]
        )

        self.assertEqual(validate_payload(payload), [])


class SeedMobilePolicyTests(TestCase):
    """
    Tests for the seed_mobile_policy command.
    """

    def test_seed_creates_the_list(self) -> None:
        """
        Tests the list matches the mobile fixture: 13 tracked, 12 usage only.
        """
        run("seed_mobile_policy")

        self.assertEqual(MobileApp.objects.count(), 25)
        self.assertEqual(MobileApp.objects.filter(tier="tracked").count(), 13)
        self.assertEqual(MobileApp.objects.filter(tier="usage_only").count(), 12)
        self.assertEqual(MobileApp.objects.filter(tier="never_log").count(), 0)
        # No screen rules yet in the app, so these are not tracked
        for package in (
            "com.instagram.android",
            "com.facebook.katana",
            "com.twitter.android",
        ):
            self.assertEqual(
                MobileApp.objects.get(package_name=package).tier, "usage_only"
            )
        self.assertEqual(
            MobileApp.objects.get(package_name="com.zhiliaoapp.musically").tier,
            "tracked",
        )

    def test_seed_is_idempotent_and_keeps_edits(self) -> None:
        """
        Tests a second run changes nothing, including edits made in the admin.
        """
        run("seed_mobile_policy")
        MobileApp.objects.filter(package_name="com.instagram.android").update(
            tier="tracked"
        )

        output = run("seed_mobile_policy")

        self.assertEqual(MobileApp.objects.count(), 25)
        self.assertEqual(
            MobileApp.objects.get(package_name="com.instagram.android").tier,
            "tracked",
        )
        self.assertIn("0 created, 0 updated, 25 skipped", output)

    def test_force_overwrites_existing_entries(self) -> None:
        """
        Tests --force puts the seeded tier back.
        """
        run("seed_mobile_policy")
        MobileApp.objects.filter(package_name="com.instagram.android").update(
            tier="tracked"
        )

        run("seed_mobile_policy", "--force")

        self.assertEqual(
            MobileApp.objects.get(package_name="com.instagram.android").tier,
            "usage_only",
        )


class PublishMobilePolicyTests(TestCase):
    """
    Tests for the publish_mobile_policy command.
    """

    def test_publish_creates_the_active_release(self) -> None:
        """
        Tests the release holds the sorted active entries and a valid hash.
        """
        create_app("com.b.app", tier="usage_only", category="email")
        create_app("com.a.app", tier="tracked", category="news")

        run("publish_mobile_policy", "--notes", "first list")

        release = MobilePolicyRelease.objects.get()
        self.assertTrue(release.is_active)
        self.assertEqual(release.notes, "first list")
        self.assertRegex(release.version, r"^\d{4}\.\d{2}\.1$")
        self.assertEqual(release.policy_hash, compute_policy_hash(release.payload))
        self.assertEqual(
            release.payload,
            {
                "schema_version": 1,
                "default_tier": "usage_only",
                "apps": [
                    {"package": "com.a.app", "tier": "tracked", "category": "news"},
                    {"package": "com.b.app", "tier": "usage_only", "category": "email"},
                ],
            },
        )

    def test_inactive_entries_are_left_out(self) -> None:
        """
        Tests a deactivated entry does not reach the release.
        """
        create_app("com.a.app", tier="tracked", category="news")
        create_app("com.off.app", tier="tracked", category="news", is_active=False)

        run("publish_mobile_policy")

        packages = [
            app["package"] for app in MobilePolicyRelease.objects.get().payload["apps"]
        ]
        self.assertEqual(packages, ["com.a.app"])

    def test_new_release_replaces_the_active_one(self) -> None:
        """
        Tests the old release is kept, inactive, and only one stays active.
        """
        app = create_app("com.a.app", tier="usage_only", category="news")
        run("publish_mobile_policy")
        app.tier = "tracked"
        app.save()

        run("publish_mobile_policy")

        self.assertEqual(MobilePolicyRelease.objects.count(), 2)
        active = MobilePolicyRelease.objects.get(is_active=True)
        self.assertRegex(active.version, r"\.2$")
        self.assertEqual(active.payload["apps"][0]["tier"], "tracked")
        old = MobilePolicyRelease.objects.get(is_active=False)
        self.assertEqual(old.payload["apps"][0]["tier"], "usage_only")

    def test_same_content_publishes_nothing(self) -> None:
        """
        Tests publishing an unchanged list does not create a release.
        """
        create_app("com.a.app", tier="tracked", category="news")
        run("publish_mobile_policy")

        output = run("publish_mobile_policy")

        self.assertEqual(MobilePolicyRelease.objects.count(), 1)
        self.assertIn("Nothing to publish", output)

    def test_dry_run_writes_nothing_and_lists_changes(self) -> None:
        """
        Tests the preview shows the changes and creates no release.
        """
        create_app("com.a.app", tier="tracked", category="news")

        output = run("publish_mobile_policy", "--dry-run")

        self.assertEqual(MobilePolicyRelease.objects.count(), 0)
        self.assertIn("ADDED    com.a.app (tracked, news)", output)
        self.assertIn("[dry-run]", output)

    def test_dry_run_shows_change_against_the_active_release(self) -> None:
        """
        Tests the preview compares with the active release.
        """
        app = create_app("com.a.app", tier="usage_only", category="news")
        create_app("com.gone.app", tier="tracked", category="news")
        run("publish_mobile_policy")
        app.tier = "tracked"
        app.save()
        MobileApp.objects.filter(package_name="com.gone.app").update(is_active=False)

        output = run("publish_mobile_policy", "--dry-run")

        self.assertIn("CHANGED  com.a.app: tier usage_only -> tracked", output)
        self.assertIn("REMOVED  com.gone.app", output)
        self.assertEqual(MobilePolicyRelease.objects.count(), 1)

    def test_invalid_entries_stop_the_publish(self) -> None:
        """
        Tests a bad tier, category or package name publishes nothing.
        """
        bad_entries = [
            {"package_name": "com.a.app", "tier": "trackd"},
            {"package_name": "com.a.app", "category": "video"},
            {"package_name": "notapackage"},
        ]
        for params in bad_entries:
            with self.subTest(params=params):
                MobileApp.objects.all().delete()
                MobileApp.objects.create(**params)

                with self.assertRaises(CommandError):
                    run("publish_mobile_policy")

                self.assertEqual(MobilePolicyRelease.objects.count(), 0)

    def test_empty_list_is_not_published(self) -> None:
        """
        Tests an empty allow-list can never become a release.
        """
        with self.assertRaises(CommandError):
            run("publish_mobile_policy")

        self.assertEqual(MobilePolicyRelease.objects.count(), 0)

    def test_version_option(self) -> None:
        """
        Tests a chosen version is used, and a taken or invalid one is refused.
        """
        create_app("com.a.app", tier="tracked", category="news")
        run("publish_mobile_policy", "--release-version", "2026.11.1")
        MobileApp.objects.update(tier="usage_only")

        self.assertEqual(MobilePolicyRelease.objects.get().version, "2026.11.1")
        for version in ("2026.11.1", "not a version", "x" * 33):
            with self.subTest(version=version), self.assertRaises(CommandError):
                run("publish_mobile_policy", "--release-version", version)

        self.assertEqual(MobilePolicyRelease.objects.count(), 1)
