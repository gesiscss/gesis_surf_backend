"""Facebook Reels index for storing Facebook reel posts."""

from elasticsearch_dsl import Boolean, Date, Integer, Keyword, Text

from .base_index import BaseIndex


class FacebookReelsIndex(BaseIndex):
    """Index for Facebook reel posts."""

    post_id = Keyword()
    author_handle = Keyword()
    author_display_name = Keyword()
    is_ad = Boolean()
    is_public = Boolean()
    content_text = Text()
    permalink = Keyword()
    post_timestamp = Date()
    post_type = Keyword()
    likes = Integer()
    comments = Integer()
    shares = Integer()
    signal_type = Keyword()
    thumbnail_url = Keyword()
    captured_at = Date()
    page_url = Keyword()
    domain_id = Keyword()

    class Index(BaseIndex.Index):
        """Elasticsearch index configuration for Facebook reels."""

        name = "facebook_reels_index"
