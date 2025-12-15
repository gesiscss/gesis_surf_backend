"""
Celery Tasks for the Domain APIs.
"""

import logging

from celery import shared_task
from core.models import Domain

logger = logging.getLogger(__name__)


def _process_html_content(html_content: str) -> str:
    """
    Process the HTML content of a snapshot.

    Args:
        html_content (str): The raw HTML content.

    Returns:
        str: The processed HTML content.
    """
    if not html_content:
        return ""

    processed_content = " ".join(html_content.split())
    return processed_content


@shared_task(bind=True, max_retries=3)
def process_domain_snapshot_task(self, domain_id: str, snapshot_html: str) -> None:
    """
    Process a domain snapshot  asynchronously.
    """

    try:
        logger.info("Processing snapshot for domain id: %s", domain_id)

        # pylint: disable=no-member
        domain = Domain.objects.get(id=domain_id)
        processed_html = _process_html_content(snapshot_html)

        domain.snapshot_html = processed_html
        domain.save(update_fields=["snapshot_html"])

    # pylint: disable=no-member
    except Domain.DoesNotExist:
        logger.warning("Domain with id %s does not exist.", domain_id)
    except Exception as exc:
        logger.error("Error processing snapshot for domain %s: %s", domain_id, str(exc))
        raise self.retry(exc=exc, countdown=2**self.request.retries) from exc
