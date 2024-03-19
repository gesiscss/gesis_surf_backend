"""
Views for the host app.
"""

from core.models import Host
from host import serializers
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


class HostViewSet(viewsets.ModelViewSet):
    """
    Manage hosts in the database.
    """

    serializer_class = serializers.HostSerializer
    # Objects available to the authenticated user.
    queryset = Host.objects.all()
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
        return self.queryset.filter(user=self.request.user).order_by("-id")

    # def get_serializer_class(self):
    #     """
    #     Return appropriate serializer class.
    #     """
    #     if self.action == "list":
    #         return serializers.HostSerializer

    #     return self.serializer_class

    # def perform_create(self, serializer):
    #     """
    #     Create a new host that belongs to the authenticated user.
    #     """
    #     serializer.save(user=self.request.user)
