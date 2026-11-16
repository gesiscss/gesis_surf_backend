"""
Twitch Stream Index for storing data from actively watched Twitch streams.
"""

from elasticsearch_dsl import Boolean, Date, Integer, Keyword, Text

from .base_index import BaseIndex


class TwitchStreamIndex(BaseIndex):
    """Index for Twitch streams actively watched on a channel page (signal_type='played')."""

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
    stream_duration = Keyword()
    captured_at = Date()
    page_url = Keyword()
    domain_id = Keyword()

    class Index(BaseIndex.Index):
        """Elasticsearch index configuration for Twitch watched streams."""

        name = "twitch_stream_index"
