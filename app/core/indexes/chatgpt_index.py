"""
Index that works with ChatGPT models
"""

from elasticsearch_dsl import Date, Integer, Keyword, Text

from .base_index import BaseIndex


class ChatGPTIndex(BaseIndex):
    """Index that works with ChatGPT models

    Args:
        BaseIndex (_type_): _description_
    """

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
        """Default settings for all indexes"""

        name = "chatgpt_index"
