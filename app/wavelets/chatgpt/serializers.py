"""
Serializers for the Wavelets APIs.
"""

from core.indexes.chatgpt_index import ChatGPTIndex
from elasticsearch.exceptions import TransportError
from rest_framework import serializers


class ChatGPTDataSerializer(serializers.Serializer):
    """
    Serializer for the ChatGPT data object.
    """

    conversation_id: serializers.CharField = serializers.CharField()
    conversation: serializers.CharField = serializers.CharField()
    timestamp: serializers.DateTimeField = serializers.DateTimeField()
    domain_id: serializers.CharField = serializers.CharField()
    message_id: serializers.CharField = serializers.CharField()
    message_type: serializers.CharField = serializers.CharField()
    turn_index: serializers.IntegerField = serializers.IntegerField()
    llm_provider: serializers.CharField = serializers.CharField()

    def create(self, validated_data: dict) -> object:
        """
        Create a new ChatGPTData instance.
        """
        try:
            doc = ChatGPTIndex(**validated_data)
            doc.save()
            return {
                **validated_data,
                "index_name": doc.get_current_index(),
                "document_id": doc.meta.id,
            }

        except TransportError as error:
            raise serializers.ValidationError({"ChatGPT error": str(error)}) from error

    def update(self, instance: object, validated_data: dict) -> object:
        """
        Update an existing ChatGPTData instance.
        """
        raise NotImplementedError("We do not support updating ChatGPT data.")
