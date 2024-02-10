"""
Views for the user app.
"""

from rest_framework import authentication
from rest_framework import generics
from rest_framework import permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from user.serializers import AuthTokenSerializer
from user.serializers import UserSerializer


class CreateUserView(generics.CreateAPIView):
    """
    Create a new user in the system.
    """

    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """
    Create a new auth token for user.
    """

    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """
    Manage the authenticated user.
    """

    serializer_class = UserSerializer
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        """
        Retrieve and return authentication user with wave information.
        """
        return self.request.user


class CreateUserWaveView(generics.CreateAPIView):
    """
    Create a new wave in the system.
    """

    serializer_class = UserSerializer
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        """
        Create a new wave.
        """
        serializer.save(user=self.request.user)
