"""
Index that works with ChatGPT models
"""

from elasticsearch_dsl import Date, Keyword, Text, Integer

from .base_index import BaseIndex


class ChatGPTIndex(BaseIndex):
    """Index that works with ChatGPT models

    Args:
        BaseIndex (_type_): _description_
    """

    conversation_id = Keyword()
    user_id = Keyword()
    conversation = Text()
    timestamp = Date()
    domain_id = Keyword()
    message_id = Keyword()
    message_type = Keyword()
    llm_provider = Keyword()
    turn_index = Integer()

    class Index:
        """Default settings for all indexes"""

        name = "chatgpt_index"
