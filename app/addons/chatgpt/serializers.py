"""
Serializers for the Addons APIs.
"""

from core.indexes.chatgpt_index import ChatGPTIndex
from elasticsearch.exceptions import TransportError
from rest_framework import serializers


class ChatGPTDataSerializer(serializers.Serializer):
    """
    Serializer for the ChatGPT data object.
    """

    user_id: str = serializers.CharField()
    conversation_id: str = serializers.CharField()
    conversation: str = serializers.CharField()
    timestamp: str = serializers.DateTimeField()

    def create(self, validated_data: dict) -> object:
        """
        Create a new ChatGPTData instance.
        """
        try:
            doc = ChatGPTIndex(**validated_data)
            doc.save()
            return doc
        except TransportError as error:
            raise serializers.ValidationError({"ChatGPT error": str(error)}) from error

    def update(self, instance: object, validated_data: dict) -> object:
        """
        Update an existing ChatGPTData instance.
        """
        raise NotImplementedError("We do not support updating ChatGPT data.")
