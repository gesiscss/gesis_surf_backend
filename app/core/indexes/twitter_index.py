"""
Index that works with X (Twitter) posts
"""

from elasticsearch_dsl import Date, Integer, Keyword, Text

from .base_index import BaseIndex


class TwitterIndex(BaseIndex):
    """Index that works with X (Twitter) posts"""

    post_id = Keyword()
    author_handle = Keyword()
    author_display_name = Keyword()
    content_text = Text()
    permalink = Keyword()
    post_timestamp = Date()
    captured_at = Date()
    replies = Integer()
    reposts = Integer()
    likes = Integer()
    bookmarks = Integer()
    views = Integer()
    page_url = Keyword()
    domain_id = Keyword()

    class Index(BaseIndex.Index):
        """Elasticsearch index configuration for X (Twitter) posts."""

        name = "twitter_index"
