"""
Management command to seed the mobile app allow-list (MobileApp entries).
Run with: python manage.py seed_mobile_policy
Use --force to overwrite the tier and category of existing entries.
"""

from core.models import MobileApp
from django.core.management.base import BaseCommand

MOBILE_APPS = [
    ("com.zhiliaoapp.musically", "tracked", "social"),
    ("de.tagesschau", "tracked", "news"),
    ("de.zeit.online", "tracked", "news"),
    ("com.netbiscuits.bild.android", "tracked", "news"),
    ("bbc.mobile.news.ww", "tracked", "news"),
    ("com.cnn.mobile.android.phone", "tracked", "news"),
    ("com.android.chrome", "tracked", "browser"),
    ("org.mozilla.firefox", "tracked", "browser"),
    ("com.sec.android.app.sbrowser", "tracked", "browser"),
    ("com.microsoft.emmx", "tracked", "browser"),
    ("com.brave.browser", "tracked", "browser"),
    ("com.opera.browser", "tracked", "browser"),
    ("com.duckduckgo.mobile.android", "tracked", "browser"),
    ("com.instagram.android", "usage_only", "social"),
    ("com.facebook.katana", "usage_only", "social"),
    ("com.facebook.lite", "usage_only", "social"),
    ("com.twitter.android", "usage_only", "social"),
    ("com.twitter.android.lite", "usage_only", "social"),
    ("com.whatsapp", "usage_only", "messenger"),
    ("org.telegram.messenger", "usage_only", "messenger"),
    ("org.thoughtcrime.securesms", "usage_only", "messenger"),
    ("com.facebook.orca", "usage_only", "messenger"),
    ("com.google.android.apps.messaging", "usage_only", "messenger"),
    ("com.google.android.gm", "usage_only", "email"),
    ("com.microsoft.office.outlook", "usage_only", "email"),
]


class Command(BaseCommand):
    """Seed the mobile app allow-list."""

    help = "Seed MobileApp entries for the mobile app allow-list."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite tier and category of existing entries.",
        )

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        force = options["force"]
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for package, tier, category in MOBILE_APPS:
            exists = MobileApp.objects.filter(package_name=package).exists()

            if exists and not force:
                self.stdout.write(
                    f"  SKIP     {package} (already exists, use --force to overwrite)"
                )
                skipped_count += 1
                continue

            _, created = MobileApp.objects.update_or_create(
                package_name=package,
                defaults={"tier": tier, "category": category, "is_active": True},
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"  CREATED  {package}"))
                created_count += 1
            else:
                self.stdout.write(self.style.WARNING(f"  UPDATED  {package}"))
                updated_count += 1

        self.stdout.write(
            f"\nDone - {created_count} created, {updated_count} updated, "
            f"{skipped_count} skipped."
        )
