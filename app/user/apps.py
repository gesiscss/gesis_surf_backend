"""
This file is used to configure the user app.
"""

from django.apps import AppConfig


class UserConfig(AppConfig):
    """User app config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "user"
