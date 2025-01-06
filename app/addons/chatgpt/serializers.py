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

    def create(self, validated_data: dict) -> object:
        """
        Create a new ChatGPTData instance.
        """
        raise NotImplementedError("We handle creation in the View.")

    def update(self, instance: object, validated_data: dict) -> object:
        """
        Update an existing ChatGPTData instance.
        """
        raise NotImplementedError("We handle updating in the View.")
