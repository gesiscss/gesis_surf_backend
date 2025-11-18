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

from .models import Extension, Host

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_extension_versions_task(self, host_id, created, old_hosts_version=None):
    """
    Update all user extensions with the new host version.

    This task is scheduled 3 hours after a Host is created or updated.

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
