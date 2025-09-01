"""
App configuration for the global session.
"""
from django.apps import AppConfig


class GlobalsessionConfig(AppConfig):
    """
    Configuration for the global session app
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "globalsession"
