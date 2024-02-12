"""
Views for the window app.
"""

from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Window
from window import serializers


class WindowViewSet(viewsets.ModelViewSet):
    """
    Manage windows in the database.
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Window.objects.all()
    serializer_class = serializers.WindowSerializer

    def get_queryset(self):
        """
        Return objects for the current authenticated user only.
        """
        return self.queryset.filter(user=self.request.user).order_by("-id")

    def perform_create(self, serializer):
        """
        Create a new window.
        """
        serializer.save(user=self.request.user)
