"""
Views for the tab app
"""

from django.db.models.query import QuerySet
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Tab
from tab import serializers


class TabViewSet(viewsets.ModelViewSet):
    """
    Manage tabs in the database.
    """

    serializer_class = serializers.TabSerializer
    # Objects available to the authenticated user.
    queryset = Tab.objects.all()
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self) -> QuerySet:
        """
        Return objects for the current authenticated user only.
        """
        return self.queryset.filter(user=self.request.user).order_by("-id")

    def perform_create(self, serializer) -> None:
        """
        Create a new tab that belongs to the authenticated user.
        """
        serializer.save(user=self.request.user)
