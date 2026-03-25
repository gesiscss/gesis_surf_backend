"""
Index that works with YouTube Shorts
"""

from elasticsearch_dsl import Date, Integer, Keyword, Text

from .base_index import BaseIndex


class YouTubeShortsIndex(BaseIndex):
    """Index that works with YouTube Shorts"""

    video_id = Keyword()
    channel_handle = Keyword()
    title = Text()
    likes = Integer()
    comments = Integer()
    video_url = Keyword()
    captured_at = Date()
    page_url = Keyword()
    domain_id = Keyword()

    class Index:
        """Elasticsearch index configuration for YouTube Shorts."""

        name = "youtube_shorts_index"
