"""
Views for the host app.
"""

from core.models import Host
from django.http import Http404
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
    lookup_field = "hostname"

    def get_queryset(self):
        """
        Return objects for the current authenticated user only.
        """
        return self.queryset.filter().order_by("-id")
