"""
Serializers for the Addons APIs.
"""

from rest_framework import serializers


class ChatGPTDataSerializer(serializers.Serializer):
    """
    Serializer for the ChatGPT data object.
    """

    user_id: str = serializers.CharField()
    conversation_id: str = serializers.CharField()
    conversation: str = serializers.CharField()
    timestamp: str = serializers.DateTimeField()
