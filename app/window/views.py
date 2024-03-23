"""
Views for the window app.
"""

from core.models import Window
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from window import serializers


class WindowViewSet(viewsets.ModelViewSet):
    """
    Manage windows in the database.
    """

    serializer_class = serializers.WindowDetailSerializer
    # Objects available to the authenticated user.
    queryset = Window.objects.all()
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

    def get_serializer_class(self):
        """
        Return appropriate serializer class.
        """
        if self.action == "list":
            return serializers.WindowSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """
        Create a new window that belongs to the authenticated user.
        """
        serializer.save(user=self.request.user)
