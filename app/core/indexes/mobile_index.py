"""
Base index for the mobile app events
"""

from typing import Any

from elasticsearch_dsl import Date, Integer, Keyword, Long, MetaField, Object

from .base_index import BaseIndex


class MobileIndex(BaseIndex):
    """Fields shared by all mobile event indexes"""

    user_id = Keyword()
    module = Keyword()
    event = Keyword()
    session_id = Keyword()
    ts = Date()
    ts_elapsed_realtime_nanos = Long()
    received_at = Date()
    app_package = Keyword()
    app_category = Keyword()
    policy_version = Keyword()
    policy_hash = Keyword()
    policy_source = Keyword()
    privacy_mode = Keyword()
    privacy_rule_id = Keyword()
    ingest_schema_version = Integer()
    app_version = Keyword()
    device_time_zone = Keyword()
    marker_id = Keyword()
    marker_type = Keyword()
    lag_nanos = Long()
    vpn_marker_elapsed_ns = Long()
    accessibility_marker_elapsed_ns = Long()
    raw = Object(enabled=False)

    class Meta:
        """Reject fields that are not declared"""

        dynamic = MetaField("strict")

    class Index(BaseIndex.Index):
        """Elasticsearch index configuration for mobile events."""

        settings: dict[str, Any] = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "30s",
            "codec": "best_compression",
        }
