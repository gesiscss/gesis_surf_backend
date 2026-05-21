"""
Facebook Feed Index for storing Facebook feed posts.
"""

from elasticsearch_dsl import Boolean, Date, Integer, Keyword, Text

from .base_index import BaseIndex


class FacebookIndex(BaseIndex):
    """Index for Facebook feed posts."""

    post_id = Keyword()
    author_handle = Keyword()
    author_display_name = Keyword()
    is_ad = Boolean()
    content_text = Text()
    permalink = Keyword()
    post_timestamp = Date()
    post_type = Keyword()
    likes = Integer()
    comments = Integer()
    shares = Integer()
    signal_type = Keyword()
    captured_at = Date()
    page_url = Keyword()
    domain_id = Keyword()

    class Index(BaseIndex.Index):
        """Elasticsearch index configuration for Facebook posts."""

        name = "facebook_index"
