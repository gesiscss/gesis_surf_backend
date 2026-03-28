"""
Django command to wait for Elasticsearch to be available
"""

import time

from django.core.management.base import BaseCommand
from django.db.utils import OperationalError
from elasticsearch_dsl import connections
from requests.exceptions import ConnectionError as RequestsConnectionError


class Command(BaseCommand):
    """Django command to wait for Elasticsearch."""

    def handle(self, *args: tuple, **options: dict) -> None:
        """Entry point for the command."""
        self.stdout.write("Waiting for Elasticsearch...")

        es_up = False
        # The default connection alias
        es_client = connections.get_connection("default")

        while not es_up:
            try:
                if es_client.ping():
                    es_up = True
                else:
                    raise OperationalError(
                        "Elasticsearch did not respond with a ping=True"
                    )
            except (RequestsConnectionError, OperationalError):
                self.stdout.write("Elasticsearch unavailable, waiting 1 second...")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Elasticsearch available!"))
