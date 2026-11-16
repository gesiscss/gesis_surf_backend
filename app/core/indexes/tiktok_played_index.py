"""
Index that works with TikTok played signals
"""

from elasticsearch_dsl import Boolean, Date, Integer, Keyword, Text

from .base_index import BaseIndex


class TikTokPlayedIndex(BaseIndex):
    """Index that works with TikTok played signals"""

    post_id = Keyword()
    feed_position = Integer()
    author_handle = Keyword()
    author_display_name = Keyword()
    is_verified = Boolean()
    is_ad = Boolean()
    content_text = Text()
    permalink = Keyword()
    music_id = Keyword()
    music_name = Keyword()
    likes = Integer()
    comments = Integer()
    shares = Integer()
    favorites = Integer()
    signal_type = Keyword()
    captured_at = Date()
    page_url = Keyword()
    domain_id = Keyword()

    class Index(BaseIndex.Index):
        """Elasticsearch index configuration for TikTok played signals."""

        name = "tiktok_played_index"
