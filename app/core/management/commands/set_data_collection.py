"""
Management command to toggle `Extension.extension_data_collection` for users.

When set to False, the browser extension will stop injecting/collecting tracking
data (clicks, scrolls, domains, tabs, windows, ...) into the backend for the
affected users.

Examples
--------
# Preview how many extensions would be affected (no writes):
python manage.py set_data_collection --value false --dry-run

# Disable data collection for ALL users (prompted to confirm):
python manage.py set_data_collection --value false

# Disable for a single user (by their user_id):
python manage.py set_data_collection --value false --user-id <gesis_user_id>

# Disable for everyone without confirmation (non-interactive, e.g. cron/CI):
python manage.py set_data_collection --value false --no-input

# Re-enable for everyone:
python manage.py set_data_collection --value true

# Filter by extension install date:
python manage.py set_data_collection --value false --installed-before 2024-01-01
python manage.py set_data_collection --value false --installed-after  2024-06-01
python manage.py set_data_collection --value false \
    --installed-after 2024-01-01 --installed-before 2024-06-01

# Filter by extension update date (e.g. recently auto-updated extensions):
python manage.py set_data_collection --value false --updated-before 2024-01-01
python manage.py set_data_collection --value false --updated-after  2024-06-01

# Combine filters (AND logic):
python manage.py set_data_collection --value false \
    --installed-after 2024-01-01 --updated-before 2024-06-01

# Target a list of user_ids from a CSV file (one user_id per line, optional header):
python manage.py set_data_collection --value false --csv users_to_disable.csv

# CSV + date filters combined (AND):
python manage.py set_data_collection --value false \
    --csv users_to_disable.csv --updated-after 2024-06-01

Notes
-----
- Uses QuerySet.update(), a single SQL UPDATE — safe for large tables (3k+ rows).
  Does NOT fire post_save signals (none are wired to Extension) and does NOT
  create django-simple-history rows. Intended for maintenance kill-switches
  where audit noise is undesirable.
- Date filters accept ISO 8601: YYYY-MM-DD or full datetime YYYY-MM-DDTHH:MM:SS.
  A bare date is interpreted as midnight (00:00:00) of that day.
- The --csv file should contain one user_id per line. A header row is allowed
  and auto-detected (skipped if the first line doesn't look like a user_id).
  Blank lines and lines starting with '#' are ignored.
"""

from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from core.models import Extension


def _parse_date(value: str, arg_name: str) -> datetime:
    """Parse an ISO 8601 date or datetime string from a CLI argument."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise CommandError(
        f"Invalid date for {arg_name}: {value!r}. "
        "Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS."
    )


def _load_user_ids_from_csv(path: str) -> list[str]:
    """Load user_ids from a CSV file (one per line).

    - A header row is auto-detected and skipped if the first non-empty line
      contains the word "user_id" (case-insensitive).
    - Blank lines and lines starting with '#' are ignored.
    - Whitespace is stripped from each value.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError as exc:
        raise CommandError(f"Could not read CSV file {path!r}: {exc}") from exc

    user_ids: list[str] = []
    for idx, raw in enumerate(lines):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # Auto-detect and skip a header row.
        if idx == 0 and "user_id" in line.lower():
            continue
        user_ids.append(line)

    if not user_ids:
        raise CommandError(f"No user_ids found in CSV file {path!r}.")

    return user_ids


class Command(BaseCommand):
    """Toggle Extension.extension_data_collection for one, many, or all users."""

    help = (
        "Set Extension.extension_data_collection to True/False for all users, "
        "a single user (--user-id), or a subset. Use --dry-run to preview."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--value",
            required=True,
            choices=["true", "false"],
            help="Target value for extension_data_collection.",
        )
        parser.add_argument(
            "--user-id",
            dest="user_id",
            default=None,
            help="Restrict the update to a single user's extension (by User.user_id).",
        )
        parser.add_argument(
            "--csv",
            dest="csv_path",
            default=None,
            help=(
                "Path to a CSV file with one user_id per line to target. "
                "A header row is auto-detected and skipped. "
                "Blank lines and lines starting with '#' are ignored."
            ),
        )
        parser.add_argument(
            "--installed-before",
            dest="installed_before",
            default=None,
            help=(
                "Only affect extensions installed before this date "
                "(YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)."
            ),
        )
        parser.add_argument(
            "--installed-after",
            dest="installed_after",
            default=None,
            help=(
                "Only affect extensions installed after this date "
                "(YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)."
            ),
        )
        parser.add_argument(
            "--updated-before",
            dest="updated_before",
            default=None,
            help=(
                "Only affect extensions updated before this date "
                "(YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)."
            ),
        )
        parser.add_argument(
            "--updated-after",
            dest="updated_after",
            default=None,
            help=(
                "Only affect extensions updated after this date "
                "(YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without writing to the database.",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            dest="no_input",
            help="Do not prompt for confirmation.",
        )

    def _build_queryset(self, options, csv_user_ids):
        """Build the Extension queryset filtered by user/date/csv criteria."""
        user_id = options["user_id"]
        installed_before = (
            _parse_date(options["installed_before"], "--installed-before")
            if options["installed_before"]
            else None
        )
        installed_after = (
            _parse_date(options["installed_after"], "--installed-after")
            if options["installed_after"]
            else None
        )
        updated_before = (
            _parse_date(options["updated_before"], "--updated-before")
            if options["updated_before"]
            else None
        )
        updated_after = (
            _parse_date(options["updated_after"], "--updated-after")
            if options["updated_after"]
            else None
        )

        qs = Extension.objects.all()
        if user_id:
            qs = qs.filter(user__user_id=user_id)
            if not qs.exists():
                raise CommandError(
                    f"No Extension found for user_id={user_id!r}."
                )
        if csv_user_ids is not None:
            qs = qs.filter(user__user_id__in=csv_user_ids)
            if not qs.exists():
                raise CommandError(
                    f"No Extension found for any of the {len(csv_user_ids)} "
                    f"user_id(s) in the CSV file."
                )
        if installed_before is not None:
            qs = qs.filter(extension_installed_at__lt=installed_before)
        if installed_after is not None:
            qs = qs.filter(extension_installed_at__gte=installed_after)
        if updated_before is not None:
            qs = qs.filter(extension_updated_at__lt=updated_before)
        if updated_after is not None:
            qs = qs.filter(extension_updated_at__gte=updated_after)

        return qs

    def _build_scope_label(self, options, csv_user_ids, csv_path):
        """Build a human-readable description of the filter scope."""
        scope_parts = []
        if options["user_id"]:
            scope_parts.append(f"user_id={options['user_id']}")
        if csv_user_ids is not None:
            scope_parts.append(f"csv={csv_path} ({len(csv_user_ids)} ids)")
        for opt_key, label in (
            ("installed_before", "installed_before"),
            ("installed_after", "installed_after"),
            ("updated_before", "updated_before"),
            ("updated_after", "updated_after"),
        ):
            if options[opt_key]:
                dt = _parse_date(options[opt_key], f"--{label}")
                scope_parts.append(f"{label}={dt.isoformat()}")
        return ", ".join(scope_parts) if scope_parts else "ALL users"

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        target_value = options["value"] == "true"
        csv_path = options["csv_path"]
        dry_run = options["dry_run"]
        no_input = options["no_input"]

        # Load user_ids from CSV if provided.
        csv_user_ids: list[str] | None = None
        if csv_path:
            csv_user_ids = _load_user_ids_from_csv(csv_path)
            self.stdout.write(
                f"Loaded {len(csv_user_ids)} user_id(s) from {csv_path}"
            )

        qs = self._build_queryset(options, csv_user_ids)
        scope_label = self._build_scope_label(options, csv_user_ids, csv_path)

        to_change = qs.filter(extension_data_collection=not target_value)
        match_count = to_change.count()
        total_count = qs.count()

        self.stdout.write(
            f"Target value: {target_value}\n"
            f"Scope: {scope_label}\n"
            f"Extensions in scope: {total_count}\n"
            f"Extensions that will change: {match_count}"
        )

        if match_count == 0:
            self.stdout.write(
                self.style.WARNING("Nothing to do — all matching rows already set.")
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.NOTICE("[dry-run] No changes written to the database.")
            )
            return

        # Confirm before a bulk change (unless --no-input).
        if not no_input:
            confirm = input(
                f"\nSet extension_data_collection={target_value} for "
                f"{match_count} extension(s) ({scope_label})? [y/N]: "
            ).strip().lower()
            if confirm not in ("y", "yes"):
                self.stdout.write(self.style.WARNING("Aborted. No changes made."))
                return

        # Single SQL UPDATE — fast, no per-row save(), no history rows.
        changed = to_change.update(extension_data_collection=target_value)
        self.stdout.write(
            self.style.SUCCESS(
                f"Updated {changed} extension(s) (bulk UPDATE, no history)."
            )
        )