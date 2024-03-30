"""
Views for the tab app
"""

from core.models import Domain, Tab
from django.db.models.query import QuerySet
from rest_framework import mixins, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from tab import serializers


class TabViewSet(viewsets.ModelViewSet):
    """
    Manage tabs in the database.
    """

    serializer_class = serializers.TabDetailSerializer
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
        return self.queryset.filter(user=self.request.user).order_by("created_at")

    def get_serializer_class(self):
        """
        Return appropriate serializer class.
        """
        if self.action == "list":
            return serializers.TabSerializer

        return self.serializer_class

    def perform_create(self, serializer) -> None:
        """
        Create a new tab that belongs to the authenticated user.
        """
        serializer.save(user=self.request.user)


class DomainViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Manage domains in the database.
    """

    serializer_class = serializers.DomainSerializer
    queryset = Domain.objects.all()
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self) -> "QuerySet":
        """
        Return objects for the current authenticated user only.
        """
        return self.queryset.filter(user=self.request.user).order_by("created_at")
