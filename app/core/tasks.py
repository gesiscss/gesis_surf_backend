"""
Celery task
"""

from celery import shared_task

from .models import Extension, Host


@shared_task
def update_extension_versions_task(host_id, created, old_hosts_version=None):
    """_summary_

    Args:
        host_id (_type_): _description_
        created (_type_): _description_
        old_hosts_version (_type_, optional): _description_. Defaults to None.
    """
    host = Host.objects.get(pk=host_id)
    if created:
        Extension.objects.update(host_version=host.hosts_version)
    elif old_hosts_version and old_hosts_version != host.hosts_version:
        Extension.objects.filter(host_version=old_hosts_version).update(
            host_version=host.hosts_version
        )
