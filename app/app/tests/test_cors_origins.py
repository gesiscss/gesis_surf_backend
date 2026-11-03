"""
Tests for env-driven CORS_ALLOWED_ORIGINS (roadmap D3).

The default origins (localhost dev URLs + the published Chrome Web
Store extension ID) must always be allowed; the CORS_ALLOWED_ORIGINS
env var appends extras; an unset or empty value must not break the
default list (RC-4 boot-crash guard).
"""

from django.test import TestCase, override_settings
from django.test.utils import isolate_apps
from importlib import reload
from unittest.mock import patch

import app.settings as app_settings

DEFAULT_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "chrome-extension://ocmaegpehmnegplnlcjnpphlpbdmdjnc",
]


class CorsOriginsSettingsTests(TestCase):
    """
    Default origins always present; env var appends; empty env safe.
    """

    def test_default_origins_present(self) -> None:
        """
        The published extension ID and localhost are always allowed.
        """
        for origin in DEFAULT_ORIGINS:
            self.assertIn(origin, app_settings.CORS_ALLOWED_ORIGINS)

    @patch.dict(
        "os.environ",
        {"CORS_ALLOWED_ORIGINS": "chrome-extension://newextensionid"},
    )
    def test_env_var_appends_extra_origin(self) -> None:
        """
        A re-published extension's new ID can be allowed via env var.
        """
        reload(app_settings)
        try:
            self.assertIn(
                "chrome-extension://newextensionid",
                app_settings.CORS_ALLOWED_ORIGINS,
            )
            for origin in DEFAULT_ORIGINS:
                self.assertIn(origin, app_settings.CORS_ALLOWED_ORIGINS)
        finally:
            reload(app_settings)

    @patch.dict("os.environ", {"CORS_ALLOWED_ORIGINS": ""})
    def test_empty_env_var_is_safe(self) -> None:
        """
        An empty CORS_ALLOWED_ORIGINS must not crash settings import
        (RC-4) and must keep the default origins.
        """
        reload(app_settings)
        try:
            self.assertEqual(
                app_settings.CORS_ALLOWED_ORIGINS, DEFAULT_ORIGINS
            )
        finally:
            reload(app_settings)

    @patch.dict(
        "os.environ",
        {"CORS_ALLOWED_ORIGINS": " , , chrome-extension://x,, "},
    )
    def test_malformed_env_entries_are_filtered(self) -> None:
        """
        Blank segments (dangling commas, spaces) are dropped safely.
        """
        reload(app_settings)
        try:
            self.assertIn("chrome-extension://x", app_settings.CORS_ALLOWED_ORIGINS)
            self.assertEqual(
                [o for o in app_settings.CORS_ALLOWED_ORIGINS if o == ""],
                [],
            )
            self.assertEqual(
                len(app_settings.CORS_ALLOWED_ORIGINS),
                len(DEFAULT_ORIGINS) + 1,
            )
        finally:
            reload(app_settings)
