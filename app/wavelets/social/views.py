"""
Views for the social wavelets API.
"""

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from wavelets.social import serializers


class SocialPostView(APIView):
    """
    API view for all social platform wavelet data.
    Accepts X (Twitter), TikTok, YouTube Shorts, and Instagram posts
    via a single endpoint, routed internally by platform + signal_type.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.SocialPostSerializer

    def post(self, request) -> Response:
        """
        Create a new social post document in the platform-specific ES index.
        """
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
