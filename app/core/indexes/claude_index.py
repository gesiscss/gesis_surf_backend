"""
Index that works with Claude models
"""

from elasticsearch_dsl import Date, Integer, Keyword, Text

from .base_index import BaseIndex


class ClaudeIndex(BaseIndex):
    """Index that works with Claude models"""

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
        """Elasticsearch index settings"""

        name = "claude_index"
