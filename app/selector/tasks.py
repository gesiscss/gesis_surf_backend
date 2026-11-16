"""
Define tasks for the selector app using Celery.
"""

from celery import shared_task
from core.models import SelectorConfig
from selector.serializers import SelectorConfigSerializer


@shared_task
def get_selectors_async() -> list[dict]:
    """
    Get all selectors.
    """
    selectors = SelectorConfig.objects.all()  # pylint: disable=no-member
    serializer = SelectorConfigSerializer(selectors, many=True)
    return serializer.data
