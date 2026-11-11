"""Selector Views"""

from celery.result import AsyncResult
from core.models import SelectorConfig
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from selector import serializers
from selector.tasks import get_selectors_async


class SelectorViewSet(viewsets.GenericViewSet):
    """
    Manage selectors in the database.
    """

    serializer_class = serializers.SelectorConfigSerializer
    queryset = SelectorConfig.objects.all()  # pylint: disable=no-member
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
    def async_selectors(self, _request):
        """
        Trigger an asynchronous task to fetch selectors and return the task ID.
        """
        task = get_selectors_async.delay()
        return Response({"task_id": task.id})

    def get_async_task_result(self, _request, task_id=None):
        """
        Get the result of an asynchronous selector task by its task ID.

        Single-use: the result is deleted from the backend (forget) right
        after it is fetched, so a task ID cannot be re-read once served.
        This is the extension's only selector fetch path, so it stays
        participant-open (audit P0 #5, A-lite decision).
        """
        task_result = AsyncResult(task_id)
        if task_result.ready():
            payload = task_result.result
            task_result.forget()
            return JsonResponse(payload, safe=False, status=200)
        return JsonResponse({"status": "Processing"}, status=202)
