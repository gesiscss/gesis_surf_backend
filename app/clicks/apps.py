"""
Configuration for the clicks app.
"""

from django.apps import AppConfig


class ClicksConfig(AppConfig):
    """Configuration for the clicks app.

    Args:
        AppConfig (_type_): The app config class.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "clicks"
