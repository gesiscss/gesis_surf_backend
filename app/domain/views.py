"""
Views for the domain app
"""

from core.models import Click, Domain, Scroll
from core.pagination import CustomPagination
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
    pagination_class = CustomPagination

    def get_queryset(self) -> QuerySet:
        """
        Return objects for the current authenticated user only.
        """
        return self.queryset.filter(user=self.request.user).order_by("-created_at")

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


class BaseDomainAttrViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Base view set for Domain attributes.
    """

    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]
    pagination_class = CustomPagination

    def get_queryset(self) -> QuerySet:
        """
        Return objects for the current authenticated user only.
        """
        return self.queryset.filter(user=self.request.user).order_by("-created_at")


class ClickViewSet(BaseDomainAttrViewSet):
    """
    Manage clicks in the database.
    """

    serializer_class = serializers.ClickSerializer
    # Objects available to the authenticated user.
    queryset = Click.objects.all()
    pagination_class = CustomPagination


class ScrollViewSet(BaseDomainAttrViewSet):
    """
    Manage scrolls in the database.
    """

    serializer_class = serializers.ScrollSerializer
    # Objects available to the authenticated user.
    queryset = Scroll.objects.all()
    pagination_class = CustomPagination
