"""
Serializers for the social wavelets API.
Handles X (Twitter), TikTok, YouTube Shorts, and Instagram posts
via a single unified endpoint routed by platform + signal_type.
"""

from core.indexes.base_index import BaseIndex
from core.indexes.instagram_index import InstagramIndex
from core.indexes.tiktok_feed_index import TikTokFeedIndex
from core.indexes.tiktok_played_index import TikTokPlayedIndex
from core.indexes.twitter_index import TwitterIndex
from core.indexes.youtube_shorts_index import YouTubeShortsIndex
from elasticsearch.exceptions import TransportError
from rest_framework import serializers

IndexClass = type[BaseIndex]

INDEX_MAPPING: dict[str, dict[str, IndexClass]] = {
    "x": {"default": TwitterIndex},
    "tiktok": {"feed": TikTokFeedIndex, "played": TikTokPlayedIndex},
    "youtube_shorts": {"default": YouTubeShortsIndex},
    "instagram": {"default": InstagramIndex},
}


class SocialPostSerializer(serializers.Serializer):
    """
    Unified serializer for all social platform wavelet data.
    Routes to the correct Elasticsearch index based on platform + signal_type.
    """

    # Core identity
    post_id = serializers.CharField()
    platform = serializers.ChoiceField(choices=list(INDEX_MAPPING.keys()))
    signal_type = serializers.CharField(allow_blank=True, default="default")

    # Author
    author_handle = serializers.CharField()
    author_display_name = serializers.CharField(allow_blank=True, default="")
    is_verified = serializers.BooleanField(default=False)

    # Content
    content_text = serializers.CharField(max_length=5000, allow_blank=True, default="")

    # Engagement
    likes = serializers.IntegerField(default=0)
    comments = serializers.IntegerField(default=0)
    shares = serializers.IntegerField(default=0)
    favorites = serializers.IntegerField(default=0)
    bookmarks = serializers.IntegerField(default=0)
    views = serializers.IntegerField(default=0)
    reposts = serializers.IntegerField(default=0)
    replies = serializers.IntegerField(default=0)

    # Media metadata (platform-specific, all optional)
    post_type = serializers.CharField(allow_blank=True, default="")
    shortcode = serializers.CharField(allow_blank=True, default="")
    music_id = serializers.CharField(allow_blank=True, default="")
    music_name = serializers.CharField(allow_blank=True, default="")
    channel_handle = serializers.CharField(allow_blank=True, default="")
    feed_position = serializers.IntegerField(default=0)

    # URLs & timestamps
    permalink = serializers.CharField()
    post_timestamp = serializers.DateTimeField(required=False, allow_null=True)
    captured_at = serializers.DateTimeField()
    page_url = serializers.CharField()
    domain_id = serializers.CharField(allow_blank=True, default="")

    def create(self, validated_data: dict) -> object:
        """
        Route to the correct index based on platform and signal_type,
        then save the document to Elasticsearch.
        """
        try:
            platform = validated_data["platform"]
            signal_type = validated_data.get("signal_type", "default")
            platform_map = INDEX_MAPPING[platform]
            index_class = platform_map.get(signal_type) or platform_map["default"]
            doc = index_class(**validated_data)
            doc.save()
            return {
                **validated_data,
                "index_name": doc.get_current_index(),
                "document_id": doc.meta.id,
            }
        except TransportError as error:
            raise serializers.ValidationError({"Social error": str(error)}) from error

    def update(self, instance: object, validated_data: dict) -> object:
        raise NotImplementedError("We do not support updating social post data.")
