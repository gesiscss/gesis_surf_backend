"""Host app configuration."""

from django.apps import AppConfig


class HostConfig(AppConfig):
    """
    Host app configuration.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "host"
