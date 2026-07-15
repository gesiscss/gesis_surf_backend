"""
Celery tasks for the core app

These tasks handle the asynchronous synchronization of host data
to user extensions, allowing extensions to download updated host
data with new categories and criteria.
"""

import logging

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError, IntegrityError

from .models import Extension, Host, SelectorConfig

logger = logging.getLogger(__name__)

HOST_VERSION_PROPAGATION_DELAY_SECONDS = 900
SELECTOR_VERSION_PROPAGATION_DELAY_SECONDS = 180


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_extension_versions_task(self, host_id, created, old_hosts_version=None):
    """
    Update all user extensions with the new host version.

    This task is scheduled after the configured host propagation delay.

    Logic:
    - If Host was CREATED: Update ALL extensions to use this new version
    - If Host was UPDATED: Update only extensions with the OLD version

    Args:
        self: Celery task context (for retries)
        host_id (UUID): The primary key of the Host instance
        created (bool): Whether the Host was newly created
        old_hosts_version (str, optional): The previous version of the Host.
            Only used for updates to target specific extensions.

    Returns:
        dict: Summary of the update operation including:
            - status: 'success', 'failed', 'skipped'
            - action: 'host_created', 'host_updated', 'version_unchanged'
            - host_id: The Host ID
            - hostname: The Host hostname
            - extension_updates: Number of extensions that were updated

    Raises:
        Exception: On database errors after all retries exhausted
    """
    try:
        # pylint: disable=no-member
        try:
            host = Host.objects.get(pk=host_id)
        except ObjectDoesNotExist:
            error_msg = f"Host with ID {host_id} does not exist"
            logger.error(error_msg)
            return {"status": "failed", "reason": error_msg, "host_id": str(host_id)}

        current_version = host.hosts_version

        # New Host created
        if created:
            logger.info(
                "Host created: ID=%s, Hostname=%s, Version=%s",
                host.id,
                host.hostname,
                current_version,
            )

            updated_count = Extension.objects.update(host_version=current_version)

            logger.info(
                "Successfully updated %d extensions to version %s for new host %s",
                updated_count,
                current_version,
                host.id,
            )

            return {
                "status": "success",
                "action": "host_created",
                "host_id": str(host.id),
                "hostname": host.hostname,
                "hosts_version": current_version,
                "extension_updates": updated_count,
                "message": f"Updated {updated_count} extensions to host version {current_version}.",
            }

        # Host updated
        # Check if we have the old version info
        if old_hosts_version is None:
            logger.warning(
                "Host %s updated but old_hosts_version is None - skipping extension update",
                host.id,
            )
            return {
                "status": "skipped",
                "reason": "old_version_missing",
                "action": "version_unknown",
                "host_id": str(host.id),
                "hostname": host.hostname,
                "hosts_version": current_version,
                "extension_updates": 0,
                "message": "Could not determine old version, skipping update.",
            }

        # Check if version actually changed
        if old_hosts_version == current_version:
            logger.info(
                "Host %s version unchanged (still %s) - skipping extension update",
                host.id,
                current_version,
            )
            return {
                "status": "skipped",
                "reason": "version_unchanged",
                "action": "version_unchanged",
                "host_id": str(host.id),
                "hostname": host.hostname,
                "hosts_version": current_version,
                "extension_updates": 0,
                "message": f"Host version unchanged at {current_version}, no update needed.",
            }

        logger.info(
            "Host %s updated: %s → %s - updating matching extensions",
            host.id,
            old_hosts_version,
            current_version,
        )

        # Set host_version to new value where it matches old value
        updated_count = Extension.objects.filter(host_version=old_hosts_version).update(
            host_version=current_version
        )

        logger.info(
            "Successfully updated %d extensions from version %s to %s for host %s",
            updated_count,
            old_hosts_version,
            current_version,
            host.id,
        )

        return {
            "status": "success",
            "action": "host_updated",
            "host_id": str(host.id),
            "hostname": host.hostname,
            "old_hosts_version": old_hosts_version,
            "new_hosts_version": current_version,
            "extension_updates": updated_count,
            "message": f"Updated {updated_count} extensions \
                from version {old_hosts_version} to {current_version}.",
        }

    except (DatabaseError, IntegrityError) as db_exc:
        error_msg = f"Database error updating extension versions for host {host_id}: {str(db_exc)}"
        logger.error(error_msg, exc_info=True)
        raise self.retry(exc=db_exc, countdown=60) from db_exc


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_selector_versions_task(self, selector_id, created, old_version=None):
    """
    Update all user extensions with the new SelectorConfig version.

    This task is scheduled after the configured selector propagation delay,
    matching the same deferred pattern used for selector version propagation.

    Logic:
    - If SelectorConfig was CREATED: Update ALL extensions to use this new version
    - If SelectorConfig was UPDATED: Update only extensions with the OLD version

    Args:
        self: Celery task context (for retries)
        selector_id (int): The primary key of the SelectorConfig instance
        created (bool): Whether the SelectorConfig was newly created
        old_version (str, optional): The previous version string.
            Only used for updates to target specific extensions.

    Returns:
        dict: Summary of the update operation including:
            - status: 'success', 'failed', 'skipped'
            - action: 'selector_created', 'selector_updated', 'version_unchanged'
            - selector_id: The SelectorConfig ID
            - extension_updates: Number of extensions that were updated

    Raises:
        Exception: On database errors after all retries exhausted
    """
    try:
        try:
            # pylint: disable=no-member
            selector = SelectorConfig.objects.get(pk=selector_id)
        except ObjectDoesNotExist:
            error_msg = f"SelectorConfig with ID {selector_id} does not exist"
            logger.error(error_msg)
            return {
                "status": "failed",
                "reason": error_msg,
                "selector_id": str(selector_id),
            }

        current_version = selector.version

        if created:
            logger.info(
                "SelectorConfig created: ID=%s, Provider=%s, Version=%s",
                selector.pk,
                selector.provider,
                current_version,
            )
            # pylint: disable=no-member
            updated_count = Extension.objects.update(selector_version=current_version)

            logger.info(
                "Successfully updated %d extensions to \
                selector_version %s for new SelectorConfig %s",
                updated_count,
                current_version,
                selector.pk,
            )

            return {
                "status": "success",
                "action": "selector_created",
                "selector_id": str(selector.pk),
                "provider": selector.provider,
                "selector_version": current_version,
                "extension_updates": updated_count,
                "message": f"Updated {updated_count} extensions to \
                    selector version {current_version}.",
            }

        if old_version is None:
            logger.warning(
                "SelectorConfig %s updated but old_version is None - skipping extension update",
                selector.pk,
            )
            return {
                "status": "skipped",
                "reason": "old_version_missing",
                "action": "version_unknown",
                "selector_id": str(selector.pk),
                "provider": selector.provider,
                "selector_version": current_version,
                "extension_updates": 0,
                "message": "Could not determine old version, skipping update.",
            }

        if old_version == current_version:
            logger.info(
                "SelectorConfig %s version unchanged (still %s) - skipping extension update",
                selector.pk,
                current_version,
            )
            return {
                "status": "skipped",
                "reason": "version_unchanged",
                "action": "version_unchanged",
                "selector_id": str(selector.pk),
                "provider": selector.provider,
                "selector_version": current_version,
                "extension_updates": 0,
                "message": f"Selector version unchanged at {current_version}, no update needed.",
            }

        logger.info(
            "SelectorConfig %s updated: %s → %s - updating matching extensions",
            selector.pk,
            old_version,
            current_version,
        )

        # pylint: disable=no-member
        updated_count = Extension.objects.filter(selector_version=old_version).update(
            selector_version=current_version
        )

        logger.info(
            "Successfully updated %d extensions  \
            from selector_version %s to %s for SelectorConfig %s",
            updated_count,
            old_version,
            current_version,
            selector.pk,
        )

        return {
            "status": "success",
            "action": "selector_updated",
            "selector_id": str(selector.pk),
            "provider": selector.provider,
            "old_version": old_version,
            "new_version": current_version,
            "extension_updates": updated_count,
            "message": f"Updated {updated_count} extensions from \
                version {old_version} to {current_version}.",
        }

    except (DatabaseError, IntegrityError) as db_exc:
        error_msg = f"Database error updating selector  \
            versions for SelectorConfig {selector_id}: {str(db_exc)}"
        logger.error(error_msg, exc_info=True)
        raise self.retry(exc=db_exc, countdown=60) from db_exc


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_selector_bundle_version_task(self, target_version):
    """Update all user extensions to the current selector bundle version."""
    try:
        # pylint: disable=no-member
        updated_count = Extension.objects.exclude(
            selector_version=target_version
        ).update(selector_version=target_version)

        logger.info(
            "Successfully updated %d extensions to selector bundle version %s",
            updated_count,
            target_version,
        )

        return {
            "status": "success",
            "action": "selector_bundle_updated",
            "selector_version": target_version,
            "extension_updates": updated_count,
            "message": (
                f"Updated {updated_count} extensions to selector version "
                f"{target_version}."
            ),
        }

    except (DatabaseError, IntegrityError) as db_exc:
        error_msg = (
            f"Database error updating selector bundle version to "
            f"{target_version}: {str(db_exc)}"
        )
        logger.error(error_msg, exc_info=True)
        raise self.retry(exc=db_exc, countdown=60) from db_exc
