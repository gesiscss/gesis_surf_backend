"""
App configuration for the addons app.
"""

from datetime import datetime

from core.indexes.chatgpt_index import ChatGPTIndex
from core.indexes.twitter_index import TwitterIndex
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from elasticsearch_dsl import connections


class AddonsConfig(AppConfig):
    """_description_

    Args:
        AppConfig (_type_): _description_
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "addons"

    def ready(self) -> None:
        """
        Set up the Elasticsearch connections and create the indices
        """

        connections.create_connection(
            alias="default",
            hosts=["http://elasticsearch:9200"],
        )

        @receiver(post_migrate)
        def create_elasticsearch_indices(
            sender: object, **kwargs: object  # pylint: disable=unused-argument
        ) -> None:
            """Starts the Elasticsearch indices as needed

            Args:
                sender (_type_): _description_
            """

            if hasattr(create_elasticsearch_indices, "_executed"):
                print("Elasticsearch indices setup already executed. Skipping.")
                return

            # pylint: disable=protected-access
            create_elasticsearch_indices._executed = True  # type: ignore

            index_classes = [
                ChatGPTIndex,
                TwitterIndex,
            ]

            current_date = datetime.now()

            for index_class in index_classes:
                print("Setting up monthly indices for:", index_class.__name__)

                index_class.create_current_month_index()

                next_months_date = self._get_next_month(current_date)
                next_index_name = index_class.get_time_based_index_name(
                    next_months_date
                )

                # pylint: disable=protected-access
                next_index_template = index_class._index.clone(name=next_index_name)

                if not next_index_template.exists():
                    next_index_template.create()
                    print(f"Created next month's index: {next_index_name}")
                else:
                    print(f"Next month's index already exists: {next_index_name}")

            print("Elasticsearch indices setup complete.")

    def _get_next_month(self, date_obj: datetime) -> datetime:
        """
        Calculate the first day of the next month based on the given date.
        """

        if date_obj.month == 12:
            return date_obj.replace(year=date_obj.year + 1, month=1, day=1)

        return date_obj.replace(month=date_obj.month + 1, day=1)
