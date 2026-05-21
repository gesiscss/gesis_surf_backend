"""
Twitch Feed Index for storing Twitch stream cards from the directory.
"""

from elasticsearch_dsl import Boolean, Date, Integer, Keyword, Text

from .base_index import BaseIndex


class TwitchFeedIndex(BaseIndex):
    """Index for Twitch stream cards seen in the directory (signal_type='feed')."""

    post_id = Keyword()
    author_handle = Keyword()
    author_display_name = Keyword()
    is_verified = Boolean()
    is_ad = Boolean()
    content_text = Text()
    permalink = Keyword()
    post_type = Keyword()
    signal_type = Keyword()
    views = Integer()
    likes = Integer()
    comments = Integer()
    viewer_count = Integer()
    is_live = Boolean()
    game_name = Keyword()
    tags = Keyword(multi=True)
    captured_at = Date()
    page_url = Keyword()
    domain_id = Keyword()

    class Index(BaseIndex.Index):
        """Elasticsearch index configuration for Twitch feed stream cards."""

        name = "twitch_feed_index"
