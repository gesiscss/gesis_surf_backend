"""
App configuration for the addons app.
"""

from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver


class AddonsConfig(AppConfig):
    """_description_

    Args:
        AppConfig (_type_): _description_
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "addons"

    def ready(self) -> None:
        """_summary_"""
        from core.indexes.chatgpt_index import (  # pylint: disable=import-outside-toplevel
            ChatGPTIndex,
        )
        from core.indexes.twitter_index import (  # pylint: disable=import-outside-toplevel
            TwitterIndex,
        )

        @receiver(post_migrate)
        def create_elasticsearch_indices(
            sender: object, **kwargs: object  # pylint: disable=unused-argument
        ) -> None:
            """Starts the Elasticsearch indices as needed

            Args:
                sender (_type_): _description_
            """
            ChatGPTIndex.init()
            TwitterIndex.init()
