"""
Django command to wait for Elasticsearch to be available
"""

import time
import os

from django.core.management.base import BaseCommand
from django.db.utils import OperationalError
from elastic_transport import ConnectionError as ElasticsearchConnectionError
from elasticsearch_dsl import connections


class Command(BaseCommand):
    """Django command to wait for Elasticsearch."""

    def handle(self, *args: tuple, **options: dict) -> None:
        """Entry point for the command."""
        self.stdout.write("Waiting for Elasticsearch...")

        es_up = False
        # The default connection alias is not configured elsewhere in this project.
        connections.create_connection(
            alias="default",
            hosts=[os.environ.get("ELASTICSEARCH_HOST", "http://elasticsearch:9200")],
        )
        es_client = connections.get_connection("default")

        while not es_up:
            try:
                if es_client.ping():
                    es_up = True
                else:
                    raise OperationalError(
                        "Elasticsearch did not respond with a ping=True"
                    )
            except (ElasticsearchConnectionError, OperationalError):
                self.stdout.write("Elasticsearch unavailable, waiting 1 second...")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Elasticsearch available!"))
