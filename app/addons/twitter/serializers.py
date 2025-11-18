"""
Serializers for Twitter data.
"""

from core.indexes.twitter_index import TwitterIndex
from elasticsearch.exceptions import TransportError
from rest_framework import serializers


class TwitterDataSerializer(serializers.Serializer):
    """
    Serializer for Twitter data object.
    """

    tweet_id: serializers.CharField = serializers.CharField(max_length=100)
    username: serializers.CharField = serializers.CharField(max_length=100)
    content: serializers.CharField = serializers.CharField()
    timestamp: serializers.DateTimeField = serializers.DateTimeField()

    def create(self, validated_data: dict) -> object:
        """
        Create a new TwitterData instance.
        """
        try:
            doc = TwitterIndex(**validated_data)
            doc.save()
            return {
                **validated_data,
                "index_name": doc.get_current_index(),
                "document_id": doc.meta.id,
            }
        except TransportError as error:
            raise serializers.ValidationError({"Twitter error": str(error)}) from error

    def update(self, instance: object, validated_data: dict) -> object:
        """
        Update an existing TwitterData instance.
        """
        raise NotImplementedError("We handle updating in the View.")
