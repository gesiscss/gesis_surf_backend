"""
Views for the tab app
"""

from django.db.models.query import QuerySet
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from core.models import Domain
from core.models import Tab
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
        return self.queryset.filter(user=self.request.user).order_by("-id")

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
        return self.queryset.filter(user=self.request.user).order_by("-id")

    # retrive all clicks for a domain
    @action(detail=True, methods=["GET"])
    def clicks(self, request, *args, **kwargs):
        """
        Retrieve all clicks for a domain.
        """
        domain = self.get_object()
        serializer = serializers.ClickSerializer(
            domain.clicks.all(), many=True
        )
        return Response(serializer.data)

    @action(detail=True, methods=["POST"])
    def add_click(self, request, *args, **kwargs):
        """
        Add a click to a domain.
        """
        domain = self.get_object()
        serializer = serializers.ClickSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(domain=domain)
            return Response(serializer.data, status=201)
        return Response(
            serializer.errors, status=400
        )
