"""
Base index for all indexes
"""

# core/indexes/base_index.py

from elasticsearch_dsl import Date, Document


class BaseIndex(Document):
    """
    Base index for all indexes
    """

    created_at = Date()
    updated_at = Date()

    class Index:
        """
        Default settings for all indexes
        """

        # Default settings; can be overridden in subclasses
        settings = {"number_of_shards": 1, "number_of_replicas": 0}
