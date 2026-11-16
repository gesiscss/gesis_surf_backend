"""
Index that works with YouTube feed videos (non-Shorts)
"""

from elasticsearch_dsl import Boolean, Date, Integer, Keyword, Text

from .base_index import BaseIndex


class YouTubeFeedIndex(BaseIndex):
    """Index that works with YouTube feed videos (non-Shorts)"""

    post_id = Keyword()
    channel_handle = Keyword()
    author_display_name = Keyword()
    is_ad = Boolean()
    content_text = Text()
    permalink = Keyword()
    post_timestamp = Date()
    post_type = Keyword()
    signal_type = Keyword()
    views = Integer()
    likes = Integer()
    comments = Integer()
    captured_at = Date()
    page_url = Keyword()
    domain_id = Keyword()

    class Index(BaseIndex.Index):
        """Elasticsearch index configuration for YouTube feed videos."""

        name = "youtube_feed_index"
