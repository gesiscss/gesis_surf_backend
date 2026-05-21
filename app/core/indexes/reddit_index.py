"""
Reddit Feed Index for storing Reddit feed posts.
"""

from elasticsearch_dsl import Boolean, Date, Integer, Keyword, Text

from .base_index import BaseIndex


class RedditIndex(BaseIndex):
    """Index for Reddit feed posts."""

    post_id = Keyword()
    author_handle = Keyword()
    author_display_name = Keyword()
    is_ad = Boolean()
    content_text = Text()
    permalink = Keyword()
    post_timestamp = Date()
    post_type = Keyword()
    signal_type = Keyword()
    likes = Integer()
    comments = Integer()
    views = Integer()
    awards = Integer()
    subreddit = Keyword()
    captured_at = Date()
    page_url = Keyword()
    domain_id = Keyword()

    class Index(BaseIndex.Index):
        """Elasticsearch index configuration for Reddit posts."""

        name = "reddit_index"
