"""
Define tasks for the host app using Celery.
"""

from celery import shared_task
from core.models import Host
from django.db.models import QuerySet
from host.serializers import HostSerializer


@shared_task
def get_hosts_async() -> QuerySet:
    """
    Get all hosts.
    """
    hosts = Host.objects.all()
    serializer = HostSerializer(hosts, many=True)
    return serializer.data
