"""
Shared rules for the mobile app allow-list policy: validation, canonical payload
and hash. The allowed values mirror the mobile app's `contract.ts`.
"""

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from typing import Any

SCHEMA_VERSION = 1
DEFAULT_TIER = "usage_only"
TIERS = ("tracked", "usage_only", "never_log")
CATEGORIES = ("news", "social", "browser", "messenger", "email", "other")

MAX_APPS = 500
MAX_PACKAGE_LENGTH = 255
MAX_VERSION_LENGTH = 32

PACKAGE_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+")
VERSION_PATTERN = re.compile(r"[A-Za-z0-9._-]+")


def build_payload(apps: Iterable[Mapping[str, str]]) -> dict[str, Any]:
    """Builds the release payload from allow-list entries, sorted by package."""
    return {
        "schema_version": SCHEMA_VERSION,
        "default_tier": DEFAULT_TIER,
        "apps": [
            {
                "package": app["package"],
                "tier": app["tier"],
                "category": app["category"],
            }
            for app in sorted(apps, key=lambda app: app["package"])
        ],
    }


def validate_payload(payload: Mapping[str, Any]) -> list[str]:
    """Returns the problems that make a payload unfit to publish (empty if valid)."""
    apps = payload["apps"]
    problems: list[str] = []

    if not apps:
        problems.append("the allow-list has no active entries")
    if len(apps) > MAX_APPS:
        problems.append(f"too many entries ({len(apps)}, maximum {MAX_APPS})")

    for app in apps:
        package = app["package"]
        if len(package) > MAX_PACKAGE_LENGTH or not PACKAGE_PATTERN.fullmatch(package):
            problems.append(f"{package!r}: invalid package name")
        if app["tier"] not in TIERS:
            problems.append(f"{package!r}: invalid tier {app['tier']!r}")
        if app["category"] not in CATEGORIES:
            problems.append(f"{package!r}: invalid category {app['category']!r}")

    return problems


def canonical_json(payload: Mapping[str, Any]) -> str:
    """Returns the canonical JSON of a payload (sorted keys, no whitespace)."""
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def compute_policy_hash(payload: Mapping[str, Any]) -> str:
    """Returns "sha256:<hex>" over the canonical JSON of the payload."""
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def describe_changes(
    old: Mapping[str, Any] | None, new: Mapping[str, Any]
) -> list[str]:
    """Describes, per app, what differs between two payloads."""
    old_apps = {app["package"]: app for app in (old or {}).get("apps", [])}
    new_apps = {app["package"]: app for app in new["apps"]}
    lines: list[str] = []

    for package in sorted(new_apps.keys() - old_apps.keys()):
        app = new_apps[package]
        lines.append(f"ADDED    {package} ({app['tier']}, {app['category']})")
    for package in sorted(old_apps.keys() - new_apps.keys()):
        lines.append(f"REMOVED  {package}")
    for package in sorted(old_apps.keys() & new_apps.keys()):
        before, after = old_apps[package], new_apps[package]
        if before != after:
            lines.append(
                f"CHANGED  {package}: tier {before['tier']} -> {after['tier']}, "
                f"category {before['category']} -> {after['category']}"
            )

    return lines
