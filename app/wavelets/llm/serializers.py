"""
Serializers for the Wavelets APIs.
"""

from core.indexes.chatgpt_index import ChatGPTIndex
from core.indexes.claude_index import ClaudeIndex
from core.indexes.deepseek_index import DeepSeekIndex
from core.indexes.gemini_index import GeminiIndex
from elasticsearch.exceptions import TransportError
from rest_framework import serializers

INDEX_MAPPING = {
    "chatgpt": ChatGPTIndex,
    "claude": ClaudeIndex,
    "deepseek": DeepSeekIndex,
    "gemini": GeminiIndex,
}


class LLMDataSerializer(serializers.Serializer):
    """
    Serializer for the LLM data object.
    """

    chat_session_id = serializers.CharField()
    message_content = serializers.CharField()
    timestamp = serializers.DateTimeField()
    domain_id = serializers.CharField(allow_blank=True, default="")
    message_id = serializers.CharField()
    message_type = serializers.CharField()
    llm_provider = serializers.ChoiceField(choices=list(INDEX_MAPPING.keys()))
    turn_index = serializers.IntegerField()
    page_title = serializers.CharField(allow_blank=True, default="")
    url = serializers.CharField(allow_blank=True, default="")

    def create(self, validated_data: dict) -> object:
        """
        Create a new LLMData instance.
        """
        try:
            provider = validated_data["llm_provider"]
            index_class = INDEX_MAPPING[provider]
            doc = index_class(**validated_data)
            doc.save()
            return {
                **validated_data,
                "index_name": doc.get_current_index(),
                "document_id": doc.meta.id,
            }

        except TransportError as error:
            raise serializers.ValidationError({"LLM error": str(error)}) from error

    def update(self, instance: object, validated_data: dict) -> object:
        """
        Update an existing LLMPTData instance.
        """
        raise NotImplementedError("We do not support updating LLMPT data.")
