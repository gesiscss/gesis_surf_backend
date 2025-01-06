"""
Views for the ChatGPT addon.
"""

from addons.chatgpt import serializers
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class ChatGPTDataView(APIView):
    """
    API view for ChatGPT data.
    """

    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = serializers.ChatGPTDataSerializer

    def post(self, request) -> Response:
        """
        Create a new ChatGPT data object.
        """
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
