"""
Views for the user app.
"""

from rest_framework import authentication, generics, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from user.serializers import AuthTokenSerializer, UserSerializer


class CreateUserView(generics.CreateAPIView):
    """
    Create a new user in the system.
    """

    serializer_class = UserSerializer
    permissions_classes = (permissions.IsAdminUser,)


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
