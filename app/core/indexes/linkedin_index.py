"""
Index that works with LinkedIn feed posts
"""

from elasticsearch_dsl import Boolean, Date, Integer, Keyword, Text

from .base_index import BaseIndex


class LinkedInIndex(BaseIndex):
    """Index that works with LinkedIn feed posts"""

    post_id = Keyword()
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
    reposts = Integer()
    signal_type = Keyword()
    # LinkedIn-specific context fields
    feed_context_type = Keyword()
    feed_context_actor = Keyword()
    feed_context_action = Keyword()
    group_name = Keyword()
    captured_at = Date()
    page_url = Keyword()
    domain_id = Keyword()

    class Index(BaseIndex.Index):
        """Elasticsearch index configuration for LinkedIn feed posts."""

        name = "linkedin_index"
