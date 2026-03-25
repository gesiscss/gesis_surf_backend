"""
Serializers for TikTok wavelet data.
"""

from core.indexes.tiktok_feed_index import TikTokFeedIndex
from core.indexes.tiktok_played_index import TikTokPlayedIndex
from elasticsearch.exceptions import TransportError
from rest_framework import serializers

INDEX_MAP = {
    "feed": TikTokFeedIndex,
    "played": TikTokPlayedIndex,
}


class TikTokDataSerializer(serializers.Serializer):
    """
    Serializer for TikTok post data. Routes to tiktok_feed_index or
    tiktok_played_index based on the signal_type field.
    """

    video_id = serializers.CharField()
    feed_position = serializers.IntegerField()
    author_handle = serializers.CharField()
    author_display_name = serializers.CharField()
    is_verified = serializers.BooleanField()
    caption = serializers.CharField(max_length=5000, allow_blank=True, default="")
    video_url = serializers.CharField()
    music_id = serializers.CharField(allow_blank=True, default="")
    music_name = serializers.CharField(allow_blank=True, default="")
    likes = serializers.IntegerField()
    comments = serializers.IntegerField()
    shares = serializers.IntegerField()
    favorites = serializers.IntegerField()
    captured_at = serializers.DateTimeField()
    page_url = serializers.CharField()
    domain_id = serializers.CharField(allow_blank=True, default="")
    signal_type = serializers.ChoiceField(choices=list(INDEX_MAP.keys()))

    def create(self, validated_data: dict) -> object:
        try:
            signal = validated_data["signal_type"]
            index_class = INDEX_MAP[signal]
            doc = index_class(**validated_data)
            doc.save()
            return {
                **validated_data,
                "index_name": doc.get_current_index(),
                "document_id": doc.meta.id,
            }
        except TransportError as error:
            raise serializers.ValidationError({"TikTok error": str(error)}) from error

    def update(self, instance: object, validated_data: dict) -> object:
        raise NotImplementedError("We do not support updating TikTok data.")
