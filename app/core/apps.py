"""
This file is used to configure the app name.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    This class is used to configure the app name.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
