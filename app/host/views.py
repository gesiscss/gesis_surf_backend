"""
Views for the host app.
"""

from celery.result import AsyncResult
from core.models import Category, Criteria, Host
from core.tasks import HOST_VERSION_PROPAGATION_DELAY_SECONDS, update_extension_versions_task
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.http import JsonResponse
from host import serializers
from host.tasks import get_hosts_async
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class HostViewSet(viewsets.ModelViewSet):
    """
    Manage hosts in the database.
    """

    serializer_class = serializers.HostSerializer
    # Objects available to the authenticated user.
    queryset = Host.objects.all()  # pylint: disable=no-member
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Return objects for the current authenticated user only.
        """
        return self.queryset.filter()

    @action(detail=False, methods=["get"])
    def async_hosts(self, _request):
        """
        Trigger an asynchronous task to fetch hosts and return the task ID.
        """
        task = get_hosts_async.delay()
        return Response({"task_id": task.id})

    def get_async_task_result(self, _request, task_id):
        """
        Endpoint to get the result of an asynchronous task by its task ID.
        """
        task_result = AsyncResult(task_id)
        if task_result.ready():
            return JsonResponse(task_result.result, safe=False, status=200)
        return JsonResponse({"status": "Processing"}, status=202)

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk_hosts(self, request):
        """
        Bulk-create hosts without firing per-row signals.

        Accepts a JSON array of host objects. Signals are disconnected for the
        duration of the insert; a single update_extension_versions_task is
        scheduled (15 min delay) at the end so extensions still get notified.

        Expected payload: list of HostSerializer-compatible dicts.
        Returns: { "created": <int>, "failed": <int>, "errors": [...] }
        """
        from core.signals import (
            capture_old_host_version,
            update_extension_versions,
        )

        items = request.data
        if not isinstance(items, list):
            return Response(
                {"detail": "Expected a JSON array."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Disconnect signals so no per-row Celery tasks are queued
        pre_save.disconnect(capture_old_host_version, sender=Host)
        post_save.disconnect(update_extension_versions, sender=Host)

        created_count = 0
        errors = []

        try:
            with transaction.atomic():
                for idx, item in enumerate(items):
                    serializer = serializers.HostSerializer(data=item)
                    if serializer.is_valid():
                        serializer.save()
                        created_count += 1
                    else:
                        errors.append({"index": idx, "errors": serializer.errors})
        finally:
            # Always reconnect signals
            pre_save.connect(capture_old_host_version, sender=Host)
            post_save.connect(update_extension_versions, sender=Host)

        # Schedule ONE task to propagate the new version to all extensions
        if created_count > 0:
            last_host = Host.objects.order_by("-created_at").first()
            if last_host:
                update_extension_versions_task.apply_async(
                    args=(str(last_host.pk), True, None),
                    countdown=HOST_VERSION_PROPAGATION_DELAY_SECONDS,
                )

        return Response(
            {
                "created": created_count,
                "failed": len(errors),
                "errors": errors[:50],  # cap error list to avoid huge responses
            },
            status=status.HTTP_201_CREATED if created_count > 0 else status.HTTP_400_BAD_REQUEST,
        )
