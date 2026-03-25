"""
Views for the TikTok wavelets API.
"""

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from wavelets.tiktok import serializers


class TikTokDataView(APIView):
    """
    API view for TikTok wavelet data.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.TikTokDataSerializer

    def post(self, request) -> Response:
        """
        Create a new TikTok data document in the signal-specific ES index.
        """
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
