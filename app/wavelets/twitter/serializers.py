"""
Serializers for X (Twitter) wavelet data.
"""

from core.indexes.twitter_index import TwitterIndex
from elasticsearch.exceptions import TransportError
from rest_framework import serializers


class TwitterDataSerializer(serializers.Serializer):
    """
    Serializer for X (Twitter) post data.
    """

    tweet_id = serializers.CharField()
    author_handle = serializers.CharField()
    author_display_name = serializers.CharField()
    tweet_text = serializers.CharField(max_length=5000)
    tweet_url = serializers.CharField()
    tweet_timestamp = serializers.DateTimeField()
    captured_at = serializers.DateTimeField()
    replies = serializers.IntegerField()
    reposts = serializers.IntegerField()
    likes = serializers.IntegerField()
    bookmarks = serializers.IntegerField()
    views = serializers.IntegerField()
    page_url = serializers.CharField()
    domain_id = serializers.CharField(allow_blank=True, default="")

    def create(self, validated_data: dict) -> object:
        try:
            doc = TwitterIndex(**validated_data)
            doc.save()
            return {
                **validated_data,
                "index_name": doc.get_current_index(),
                "document_id": doc.meta.id,
            }
        except TransportError as error:
            raise serializers.ValidationError({"X error": str(error)}) from error

    def update(self, instance: object, validated_data: dict) -> object:
        raise NotImplementedError("We do not support updating X data.")
