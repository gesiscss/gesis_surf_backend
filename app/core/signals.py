"""
Singals for the core app
"""

import logging

from celery.exceptions import OperationalError
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Host, SelectorConfig
from .tasks import (
    HOST_VERSION_PROPAGATION_DELAY_SECONDS,
    SELECTOR_VERSION_PROPAGATION_DELAY_SECONDS,
    update_extension_versions_task,
    update_selector_versions_task,
)

logger = logging.getLogger(__name__)

_host_old_versions: dict[int, str | None] = {}
_selector_old_versions: dict[int, str | None] = {}


@receiver(pre_save, sender=Host)
def capture_old_host_version(
    sender, instance, **kwargs
):  # pylint: disable=unused-argument
    """
    Signal to capture the old version of the host before it is saved.

    Args:
        sender (_type_): The model class
        instance (_type_): The instance being saved
    """
    # pylint: disable=no-member
    if instance.pk:
        try:
            old_instance = Host.objects.get(pk=instance.pk)
            _host_old_versions[instance.pk] = old_instance.hosts_version
            logger.info(
                "Captured old hosts_version for host %s: %s",
                instance.pk,
                old_instance.hosts_version,
            )
        except Host.DoesNotExist:
            logger.warning(
                "Host with pk %s does not exist. Cannot capture old hosts_version.",
                instance.pk,
            )
            _host_old_versions[instance.pk] = None


# pylint: disable=unused-argument
@receiver(post_save, sender=Host)
def update_extension_versions(sender, instance, created, update_fields, **kwargs):
    """
    Signal to update extension versions when a host is created or updated
    This works with a countdown of 15 minutes to avoid multiple updates in a short period of time.

    Args:
        sender (_type_): The model class
        instance (_type_): The instance being created or updated
        created (_type_): Whether the instance was created or updated
        update_fields (_type_): The fields that were updated
    """

    old_version = _host_old_versions.pop(instance.pk, None) if instance.pk else None

    if not created and update_fields and "hosts_version" not in update_fields:
        logger.info("Skipping update_extension_versions_task for host %s", instance.pk)
        return

    action = "created" if created else "updated"
    logger.info(
        "Host %s (%s) %s - version: %s (old: %s)",
        instance.pk,
        instance.hostname,
        action,
        instance.hosts_version,
        old_version or "N/A",
    )

    try:
        task = update_extension_versions_task.apply_async(  # type: ignore
            args=(instance.pk, created, old_version),
            countdown=HOST_VERSION_PROPAGATION_DELAY_SECONDS,
            description=f"Update extension versions for host {instance.pk}",
        )

        logger.info(
            "Scheduled update_extension_versions_task for host %s in 15 minutes. Task ID: %s",
            instance.pk,
            task.id,
        )
    except OperationalError as exception:
        logger.error(
            "Celery broker scheduling failed for host %s: %s",
            instance.pk,
            str(exception),
        )

    except RuntimeError as exception:
        logger.error(
            "Celery runtime error scheduling failed for host %s: %s",
            instance.pk,
            str(exception),
        )

    except ValueError as exception:
        logger.error(
            "Celery value error scheduling failed for host %s: %s",
            instance.pk,
            str(exception),
        )


@receiver(pre_save, sender=SelectorConfig)
def capture_old_selector_version(
    sender, instance, **kwargs
):  # pylint: disable=unused-argument
    """
    Signal to capture the old version of the SelectorConfig before it is saved.

    Args:
        sender (_type_): The model class
        instance (_type_): The instance being saved
    """
    if instance.pk:
        try:
            # pylint: disable=no-member
            old_instance = SelectorConfig.objects.get(pk=instance.pk)
            _selector_old_versions[instance.pk] = old_instance.version
            logger.info(
                "Captured old version for SelectorConfig %s (%s): %s",
                instance.pk,
                instance.provider,
                old_instance.version,
            )
        except SelectorConfig.DoesNotExist:
            logger.warning(
                "SelectorConfig with pk %s does not exist. Cannot capture old version.",
                instance.pk,
            )
            _selector_old_versions[instance.pk] = None


# pylint: disable=unused-argument
@receiver(post_save, sender=SelectorConfig)
def update_extension_selector_versions(
    sender, instance, created, update_fields, **kwargs
):
    """
    Signal to update extension selector_version when a SelectorConfig is created or updated.
    Deferred 5 minutes via Celery, matching the selector propagation pattern.

    Args:
        sender (_type_): The model class
        instance (_type_): The instance being created or updated
        created (_type_): Whether the instance was created or updated
        update_fields (_type_): The fields that were updated
    """
    old_version = _selector_old_versions.pop(instance.pk, None) if instance.pk else None

    if not created and update_fields and "version" not in update_fields:
        logger.info(
            "Skipping update_selector_versions_task for SelectorConfig %s", instance.pk
        )
        return

    action = "created" if created else "updated"
    logger.info(
        "SelectorConfig %s (%s) %s - version: %s (old: %s)",
        instance.pk,
        instance.provider,
        action,
        instance.version,
        old_version or "N/A",
    )

    try:
        task = update_selector_versions_task.apply_async(  # type: ignore
            args=(instance.pk, created, old_version),
            countdown=SELECTOR_VERSION_PROPAGATION_DELAY_SECONDS,
            description=f"Update selector versions for SelectorConfig {instance.pk}",
        )
        logger.info(
            "Scheduled update_selector_versions_task for SelectorConfig %s in 5 minutes. Task ID: %s",
            instance.pk,
            task.id,
        )
    except OperationalError as exception:
        logger.error(
            "Celery broker scheduling failed for SelectorConfig %s: %s",
            instance.pk,
            str(exception),
        )
    except RuntimeError as exception:
        logger.error(
            "Celery runtime error for SelectorConfig %s: %s",
            instance.pk,
            str(exception),
        )
    except ValueError as exception:
        logger.error(
            "Celery value error for SelectorConfig %s: %s",
            instance.pk,
            str(exception),
        )
