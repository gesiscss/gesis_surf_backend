"""
Serializers for the social wavelets API.
Handles X (Twitter), TikTok, YouTube Shorts, and Instagram posts
via a single unified endpoint routed by platform + signal_type.
"""

from core.indexes.base_index import BaseIndex
from core.indexes.facebook_index import FacebookIndex
from core.indexes.instagram_index import InstagramIndex
from core.indexes.linkedin_index import LinkedInIndex
from core.indexes.reddit_index import RedditIndex
from core.indexes.threads_index import ThreadsIndex
from core.indexes.tiktok_feed_index import TikTokFeedIndex
from core.indexes.tiktok_played_index import TikTokPlayedIndex
from core.indexes.twitch_feed_index import TwitchFeedIndex
from core.indexes.twitch_stream_index import TwitchStreamIndex
from core.indexes.twitter_index import TwitterIndex
from core.indexes.youtube_feed_index import YouTubeFeedIndex
from core.indexes.youtube_shorts_index import YouTubeShortsIndex
from core.indexes.youtube_watch_index import YouTubeWatchIndex
from elasticsearch.exceptions import TransportError
from rest_framework import serializers

IndexClass = type[BaseIndex]

INDEX_MAPPING: dict[str, dict[str, IndexClass]] = {
    "x": {"feed": TwitterIndex},
    "tiktok": {"feed": TikTokFeedIndex, "played": TikTokPlayedIndex},
    "youtube": {"feed": YouTubeFeedIndex, "played": YouTubeWatchIndex},
    "youtube_shorts": {"feed": YouTubeShortsIndex},
    "instagram": {"feed": InstagramIndex},
    "linkedin": {"feed": LinkedInIndex},
    "facebook": {"feed": FacebookIndex},
    "reddit": {"feed": RedditIndex},
    "threads": {"feed": ThreadsIndex},
    "twitch": {"feed": TwitchFeedIndex, "played": TwitchStreamIndex},
}


class SocialPostSerializer(serializers.Serializer):
    """
    Unified serializer for all social platform wavelet data.
    Routes to the correct Elasticsearch index based on platform + signal_type.
    """

    # Core identity
    post_id = serializers.CharField()
    platform = serializers.ChoiceField(choices=list(INDEX_MAPPING.keys()))
    signal_type = serializers.CharField(allow_blank=True, default="feed")

    # Author
    author_handle = serializers.CharField()
    author_display_name = serializers.CharField(allow_blank=True, default="")
    is_verified = serializers.BooleanField(default=False)
    is_ad = serializers.BooleanField(default=False)

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
    # LinkedIn-specific
    feed_context_type = serializers.CharField(allow_blank=True, default="")
    feed_context_actor = serializers.CharField(allow_blank=True, default="")
    feed_context_action = serializers.CharField(allow_blank=True, default="")
    group_name = serializers.CharField(allow_blank=True, default="")

    # URLs & timestamps
    permalink = serializers.CharField()
    post_timestamp = serializers.DateTimeField(required=False, allow_null=True)
    captured_at = serializers.DateTimeField()
    page_url = serializers.CharField()
    domain_id = serializers.CharField(allow_blank=True, default="")

    # Reddit-specific
    subreddit = serializers.CharField(allow_blank=True, default="")
    awards = serializers.IntegerField(default=0)

    # Twitch-specific
    viewer_count = serializers.IntegerField(default=0)
    is_live = serializers.BooleanField(default=False)
    game_name = serializers.CharField(allow_blank=True, default="")
    tags = serializers.ListField(child=serializers.CharField(), default=list)
    stream_duration = serializers.CharField(allow_blank=True, default="")

    def _index_field_names(self, index_class: IndexClass) -> set[str]:
        """Return the set of field names declared on the given index class."""
        # pylint: disable=protected-access
        mapping_dict = index_class._doc_type.mapping.to_dict()
        return set(mapping_dict.get("properties", {}).keys())

    def create(self, validated_data: dict) -> object:
        """
        Route to the correct index based on platform and signal_type,
        then save the document to Elasticsearch.
        Only fields declared on the target index are passed to avoid
        dynamic mapping pollution from platform-specific fields.
        """
        try:
            platform = validated_data["platform"]
            signal_type = validated_data.get("signal_type", "feed")
            platform_map = INDEX_MAPPING[platform]
            index_class = platform_map.get(signal_type) or platform_map["feed"]
            allowed = self._index_field_names(index_class)
            doc_data = {k: v for k, v in validated_data.items() if k in allowed}
            doc = index_class(**doc_data)
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
