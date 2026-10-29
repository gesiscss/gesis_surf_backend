"""
Management command to publish the active MobileApp entries as a new mobile
policy release and make it the active one.
Run with: python manage.py publish_mobile_policy
Use --dry-run to preview the changes, --release-version to choose the version.
"""

from core.mobile_policy import (
    MAX_VERSION_LENGTH,
    VERSION_PATTERN,
    build_payload,
    compute_policy_hash,
    describe_changes,
    validate_payload,
)
from core.models import MobileApp, MobilePolicyRelease
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

MAX_REPORTED_PROBLEMS = 20


class Command(BaseCommand):
    """Publish the active MobileApp entries as a new mobile policy release."""

    help = (
        "Publish the active MobileApp entries as the new active mobile policy "
        "release. Use --dry-run to preview the changes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--release-version",
            dest="release_version",
            default=None,
            help="Release version (default: YYYY.MM.N for the current month).",
        )
        parser.add_argument(
            "--notes",
            default="",
            help="Free-text notes stored with the release.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without writing to the database.",
        )

    def _resolve_version(self, requested: str | None) -> str:
        """Validate the requested version, or pick the next one of this month."""
        if requested is not None:
            if len(requested) > MAX_VERSION_LENGTH or not VERSION_PATTERN.fullmatch(
                requested
            ):
                raise CommandError(
                    f"Invalid version {requested!r}: use letters, digits, '.', '_' "
                    f"or '-', at most {MAX_VERSION_LENGTH} characters."
                )
            if MobilePolicyRelease.objects.filter(version=requested).exists():
                raise CommandError(f"A release with version {requested!r} exists.")
            return requested

        prefix = timezone.now().strftime("%Y.%m")
        number = MobilePolicyRelease.objects.filter(
            version__startswith=f"{prefix}."
        ).count()
        while True:
            number += 1
            candidate = f"{prefix}.{number}"
            if not MobilePolicyRelease.objects.filter(version=candidate).exists():
                return candidate

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        entries = [
            {
                "package": app["package_name"],
                "tier": app["tier"],
                "category": app["category"],
            }
            for app in MobileApp.objects.filter(is_active=True).values(
                "package_name", "tier", "category"
            )
        ]
        payload = build_payload(entries)

        problems = validate_payload(payload)
        if problems:
            shown = "\n".join(
                f"  - {line}" for line in problems[:MAX_REPORTED_PROBLEMS]
            )
            raise CommandError(
                f"Cannot publish, {len(problems)} problem(s) found:\n{shown}"
            )

        policy_hash = compute_policy_hash(payload)
        active = MobilePolicyRelease.objects.filter(is_active=True).first()

        if active is not None and active.policy_hash == policy_hash:
            self.stdout.write(
                self.style.WARNING(
                    f"Nothing to publish: the active release {active.version} "
                    "already has this content."
                )
            )
            return

        version = self._resolve_version(options["release_version"])
        tier_counts = ", ".join(
            f"{tier} {sum(1 for app in payload['apps'] if app['tier'] == tier)}"
            for tier in ("tracked", "usage_only", "never_log")
        )
        self.stdout.write(
            f"Version: {version}\n"
            f"Hash: {policy_hash}\n"
            f"Apps: {len(payload['apps'])} ({tier_counts})\n"
            f"Compared with: {active.version if active else 'no active release'}"
        )
        for line in describe_changes(active.payload if active else None, payload):
            self.stdout.write(f"  {line}")

        if options["dry_run"]:
            self.stdout.write(
                self.style.NOTICE("[dry-run] No changes written to the database.")
            )
            return

        with transaction.atomic():
            MobilePolicyRelease.objects.filter(is_active=True).update(is_active=False)
            MobilePolicyRelease.objects.create(
                version=version,
                policy_hash=policy_hash,
                payload=payload,
                is_active=True,
                notes=options["notes"],
            )

        self.stdout.write(self.style.SUCCESS(f"Published release {version}."))
