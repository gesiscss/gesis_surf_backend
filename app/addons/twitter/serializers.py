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

    tweet_id = serializers.CharField(max_length=100)
    username = serializers.CharField(max_length=100)
    content = serializers.CharField()
    timestamp = serializers.DateTimeField()

    def create(self, validated_data: dict) -> object:
        """
        Create a new TwitterData instance.
        """
        try:
            doc = TwitterIndex(**validated_data)
            doc.save()
            return doc
        except TransportError as error:
            raise serializers.ValidationError({"Twitter error": str(error)}) from error

    def update(self, instance: object, validated_data: dict) -> object:
        """
        Update an existing TwitterData instance.
        """
        raise NotImplementedError("We handle updating in the View.")
