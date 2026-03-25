"""
Index that works with TikTok feed signals
"""

from elasticsearch_dsl import Boolean, Date, Integer, Keyword, Text

from .base_index import BaseIndex


class TikTokFeedIndex(BaseIndex):
    """Index that works with TikTok feed signals"""

    video_id = Keyword()
    feed_position = Integer()
    author_handle = Keyword()
    author_display_name = Keyword()
    is_verified = Boolean()
    caption = Text()
    video_url = Keyword()
    music_id = Keyword()
    music_name = Keyword()
    likes = Integer()
    comments = Integer()
    shares = Integer()
    favorites = Integer()
    captured_at = Date()
    page_url = Keyword()
    domain_id = Keyword()
    signal_type = Keyword()

    class Index:
        """Elasticsearch index configuration for TikTok feed signals."""

        name = "tiktok_feed_index"
