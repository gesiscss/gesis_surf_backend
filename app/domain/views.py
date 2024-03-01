"""
Views for the domain app
"""

from core.models import Click, Domain, Scroll
from django.db.models.query import QuerySet
from domain import serializers
from rest_framework import mixins, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


class DomainViewSet(viewsets.ModelViewSet):
    """
    Manage domains in the database.
    """

    serializer_class = serializers.DomainDetailSerializer
    # Objects available to the authenticated user.
    queryset = Domain.objects.all()
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

    def get_serializer_class(self):
        """
        Return appropriate serializer class.
        """
        if self.action == "list":
            return serializers.DomainSingleSerializer

        return self.serializer_class

    def perform_create(self, serializer) -> None:
        """
        Create a new domain that belongs to the authenticated user.
        """
        serializer.save(user=self.request.user)


class ClickViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Manage clicks in the database.
    """

    serializer_class = serializers.ClickSerializer
    # Objects available to the authenticated user.
    queryset = Click.objects.all()
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


class ScrollViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Manage scrolls in the database.
    """

    serializer_class = serializers.ScrollSerializer
    # Objects available to the authenticated user.
    queryset = Scroll.objects.all()
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
