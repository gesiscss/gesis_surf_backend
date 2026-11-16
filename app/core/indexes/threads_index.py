"""
Threads Feed Index for storing Threads feed posts.
"""

from elasticsearch_dsl import Boolean, Date, Integer, Keyword, Text

from .base_index import BaseIndex


class ThreadsIndex(BaseIndex):
    """Index for Threads feed posts."""

    post_id = Keyword()
    author_handle = Keyword()
    author_display_name = Keyword()
    is_verified = Boolean()
    is_ad = Boolean()
    content_text = Text()
    permalink = Keyword()
    post_timestamp = Date()
    signal_type = Keyword()
    likes = Integer()
    comments = Integer()
    reposts = Integer()
    replies = Integer()
    captured_at = Date()
    page_url = Keyword()
    domain_id = Keyword()

    class Index(BaseIndex.Index):
        """Elasticsearch index configuration for Threads posts."""

        name = "threads_index"
