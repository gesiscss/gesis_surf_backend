"""
Index that works with YouTube Shorts
"""

from elasticsearch_dsl import Date, Integer, Keyword, Text

from .base_index import BaseIndex


class YouTubeShortsIndex(BaseIndex):
    """Index that works with YouTube Shorts"""

    post_id = Keyword()
    channel_handle = Keyword()
    content_text = Text()
    permalink = Keyword()
    likes = Integer()
    comments = Integer()
    captured_at = Date()
    page_url = Keyword()
    domain_id = Keyword()

    class Index(BaseIndex.Index):
        """Elasticsearch index configuration for YouTube Shorts."""

        name = "youtube_shorts_index"
