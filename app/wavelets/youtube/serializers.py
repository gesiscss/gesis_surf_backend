"""
Serializers for YouTube Shorts wavelet data.
"""

from core.indexes.youtube_shorts_index import YouTubeShortsIndex
from elasticsearch.exceptions import TransportError
from rest_framework import serializers


class YouTubeShortsDataSerializer(serializers.Serializer):
    """
    Serializer for YouTube Shorts data.
    """

    video_id = serializers.CharField()
    channel_handle = serializers.CharField(allow_blank=True, default="")
    title = serializers.CharField(max_length=500, allow_blank=True, default="")
    likes = serializers.IntegerField()
    comments = serializers.IntegerField()
    video_url = serializers.CharField()
    captured_at = serializers.DateTimeField()
    page_url = serializers.CharField()
    domain_id = serializers.CharField(allow_blank=True, default="")

    def create(self, validated_data: dict) -> object:
        try:
            doc = YouTubeShortsIndex(**validated_data)
            doc.save()
            return {
                **validated_data,
                "index_name": doc.get_current_index(),
                "document_id": doc.meta.id,
            }
        except TransportError as error:
            raise serializers.ValidationError({"YouTube error": str(error)}) from error

    def update(self, instance: object, validated_data: dict) -> object:
        raise NotImplementedError("We do not support updating YouTube Shorts data.")
