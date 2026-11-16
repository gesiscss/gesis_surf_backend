"""
Instagram Index that works with Instagram posts
"""

from elasticsearch_dsl import Boolean, Date, Integer, Keyword, Text

from .base_index import BaseIndex


class InstagramIndex(BaseIndex):
    """Index that works with Instagram posts"""

    post_id = Keyword()
    shortcode = Keyword()
    author_handle = Keyword()
    author_display_name = Keyword()
    is_verified = Boolean()
    is_ad = Boolean()
    content_text = Text()
    permalink = Keyword()
    post_timestamp = Date()
    post_type = Keyword()
    likes = Integer()
    comments = Integer()
    captured_at = Date()
    page_url = Keyword()
    domain_id = Keyword()

    class Index(BaseIndex.Index):
        """Elasticsearch index configuration for Instagram posts."""

        name = "instagram_index"
