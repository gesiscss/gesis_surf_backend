"""
Views for the LLM wavelets API.
"""

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from wavelets.llm import serializers


class LLMDataView(APIView):
    """
    API view for LLM wavelet data (ChatGPT, Claude, DeepSeek, Gemini).
    """

    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = serializers.LLMDataSerializer

    def post(self, request) -> Response:
        """
        Create a new LLM data document in the provider-specific ES index.
        """
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
