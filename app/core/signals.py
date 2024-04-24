"""
Singals for the core app
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Host
from .tasks import update_extension_versions_task


# pylint: disable=unused-argument
@receiver(post_save, sender=Host)
def update_extension_versions(sender, instance, created, **kwargs):
    """_summary_

    Args:
        sender (_type_): _description_
        instance (_type_): _description_
        created (_type_): _description_
    """
    old_hosts_version = None
    if not created:
        old_host = Host.objects.get(pk=instance.pk)
        old_hosts_version = old_host.hosts_version
    update_extension_versions_task.apply_async(
        (instance.pk, created, old_hosts_version), countdown=10800
    )


# # pylint: disable=unused-argument
# @receiver(post_save, sender=Host)
# def update_extension_versions(sender, instance, created, **kwargs):
#     """_summary_

#     Args:
#         sender (_type_): _description_
#         instance (_type_): _description_
#         created (_type_): _description_
#     """
#     if created:
#         Extension.objects.update(host_version=instance.hosts_version)
#     else:
#         old_host = Host.objects.get(pk=instance.pk)
#         if old_host.hosts_version != instance.hosts_version:
#             Extension.objects.filter(host_version=old_host.hosts_version).update(
#                 host_version=instance.hosts_version
#             )
