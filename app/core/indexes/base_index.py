"""
Base index for all indexes
"""

from datetime import datetime, timezone

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

    @classmethod
    def get_time_based_index_name(cls, date_obj=None) -> str:
        """
        Generate a time-based index name based on the current date.
        Format: base_index_YYYY_MM
        """

        if date_obj is None:
            date_obj = datetime.now(timezone.utc)

        # pylint: disable=protected-access
        base_name = cls._index._name
        year_month = date_obj.strftime("%Y_%m")

        return f"{base_name}_{year_month}"

    @classmethod
    def get_current_index(cls) -> str:
        """
        Get the current time-based index name.
        """

        return cls.get_time_based_index_name()

    @classmethod
    def create_current_month_index(cls) -> str:
        """
        Create the index for the current month if it doesn't exist.
        """

        current_index_name = cls.get_current_index()
        index_template = cls._index.clone(name=current_index_name)

        if not index_template.exists():
            index_template.create()
            print(f"Created monthly index: {current_index_name}")
        else:
            print(f"Monthly index already exists: {current_index_name}")

        return current_index_name

    # pylint: disable=too-many-arguments
    def save(
        self,
        using=None,
        index=None,
        validate=True,
        skip_empty=True,
        return_doc_meta=False,
        **kwargs,
    ) -> str:
        """
        Override save to set timestamps.
        """
        now = datetime.now(timezone.utc)

        if not self.created_at:
            self.created_at = now  # type: ignore[assignment]
        self.updated_at = now  # type: ignore[assignment]

        if index is None:
            index = self.get_current_index()

        try:
            return super().save(
                using=using,
                index=index,
                validate=validate,
                skip_empty=skip_empty,
                return_doc_meta=return_doc_meta,
                **kwargs,
            )
        except Exception as error:
            error_str = str(error).lower()
            if any(
                term in error_str
                for term in [
                    "index not found",
                    "indexmissingexception",
                    "no such index",
                    "404",
                ]
            ):
                self.create_current_month_index()
                return super().save(
                    using=using,
                    index=index,
                    validate=validate,
                    skip_empty=skip_empty,
                    return_doc_meta=return_doc_meta,
                    **kwargs,
                )
            raise
