"""
Views for the host app.
"""

from celery.result import AsyncResult
from core.models import Host
from django.http import JsonResponse
from host import serializers
from host.tasks import get_hosts_async
from rest_framework import viewsets
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
