"""
Configuration for the scrolls app.
"""

from django.apps import AppConfig


class ScrollsConfig(AppConfig):
    """Configuration for the scrolls app.

    Args:
        AppConfig (_type_): The app config class.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "scrolls"
