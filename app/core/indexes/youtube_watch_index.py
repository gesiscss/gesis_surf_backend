"""
YouTube Watch Index for storing data from watched YouTube videos (/watch page).
"""

from elasticsearch_dsl import Boolean, Date, Integer, Keyword, Text

from .base_index import BaseIndex


class YouTubeWatchIndex(BaseIndex):
    """Index for YouTube videos that were actively watched (signal_type='played')."""

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
        """Elasticsearch index configuration for YouTube watched videos."""

        name = "youtube_watch_index"
