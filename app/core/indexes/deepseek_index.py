"""
Index that works with DeepSeek models
"""

from elasticsearch_dsl import Date, Integer, Keyword, Text

from .base_index import BaseIndex


class DeepSeekIndex(BaseIndex):
    """Index that works with DeepSeek models"""

    chat_session_id = Keyword()
    message_content = Text()
    timestamp = Date()
    domain_id = Keyword()
    message_id = Keyword()
    message_type = Keyword()
    llm_provider = Keyword()
    turn_index = Integer()
    page_title = Text()
    url = Keyword()

    class Index:
        """Elasticsearch index configuration for DeepSeek data."""

        name = "deepseek_index"
