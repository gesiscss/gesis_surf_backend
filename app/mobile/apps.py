"""
App configuration for the mobile app.
"""

from datetime import datetime, timedelta, timezone

from core.indexes.mobile_accessibility_index import (
    MobileAccessibilityAppIndex,
    MobileAccessibilityBrowserIndex,
)
from core.indexes.mobile_vpn_index import (
    MobileVpnAppIndex,
    MobileVpnBrowserIndex,
)
from django.apps import AppConfig, apps
from django.db.models.signals import post_migrate

INDEX_CLASSES = [
    MobileAccessibilityAppIndex,
    MobileAccessibilityBrowserIndex,
    MobileVpnAppIndex,
    MobileVpnBrowserIndex,
]


def create_elasticsearch_indices(**_kwargs: object) -> None:
    """
    Create the indexes of this month and the next one if they do not exist.
    """
    first_of_month = datetime.now(timezone.utc).replace(day=1)
    next_month = (first_of_month + timedelta(days=32)).replace(day=1)

    for index_class in INDEX_CLASSES:
        index_class.create_current_month_index()

        # pylint: disable=protected-access
        next_index = index_class._index.clone(
            name=index_class.get_time_based_index_name(next_month)
        )
        if not next_index.exists():
            next_index.create()


class MobileConfig(AppConfig):
    """
    Mobile app configuration.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "mobile"

    def ready(self) -> None:
        """
        Create the Elasticsearch indexes once the migrations have run.
        """
        post_migrate.connect(
            create_elasticsearch_indices,
            sender=apps.get_app_config("core"),
            dispatch_uid="mobile_create_elasticsearch_indices",
        )
