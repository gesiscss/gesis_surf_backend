"""
Views for the YouTube Shorts wavelets API.
"""

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from wavelets.youtube import serializers


class YouTubeShortsDataView(APIView):
    """
    API view for YouTube Shorts wavelet data.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.YouTubeShortsDataSerializer

    def post(self, request) -> Response:
        """
        Create a new YouTube Shorts data document in the ES index.
        """
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
