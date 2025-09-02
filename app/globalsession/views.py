"""
Views for the global session app
"""

from core.models import GlobalSession
from globalsession import serializers
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


class GlobalSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for the GlobalSession model
    """
    
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    queryset = GlobalSession.objects.all()
    serializer_class = serializers.GlobalSessionSerializer

    def get_queryset(self):
        """Get the list of all global sessions for the authenticated user.

        Returns:
            QuerySet: A queryset of global sessions.
        """
        return super().get_queryset().filter(user=self.request.user)

    def get_serializer_class(self):
        """Get the serializer class for the viewset.

        Returns:
            Type[serializers.BaseSerializer]: The serializer class to use.
        """
        return serializers.GlobalSessionSerializer

    def perform_create(self, serializer):
        """Create a new global session for the authenticated user.

        Args:
            serializer (serializers.GlobalSessionSerializer): The serializer instance.
        """
        serializer.save(user=self.request.user)
