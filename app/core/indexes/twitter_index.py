"""
Document for twitter index
"""

from elasticsearch_dsl import Date, Keyword, Text

from .base_index import BaseIndex


class TwitterIndex(BaseIndex):
    """Document for twitter index

    Args:
        BaseIndex (_type_): _description_
    """

    tweet_id = Keyword()
    username = Keyword()
    content = Text()
    timestamp = Date()

    class Index:
        """
        Default settings for all indexes
        """

        name = "twitter_index"
