"""
App configuration for the mobile app.
"""

from django.apps import AppConfig


class MobileConfig(AppConfig):
    """
    Mobile app configuration.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "mobile"
