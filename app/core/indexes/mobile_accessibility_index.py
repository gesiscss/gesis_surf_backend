"""
Indexes that work with mobile accessibility events
"""

from elasticsearch_dsl import (
    Boolean,
    Date,
    Float,
    Integer,
    Keyword,
    Long,
    Object,
    Text,
)

from .mobile_index import MobileIndex


class MobileAccessibilityIndex(MobileIndex):
    """Fields shared by the mobile accessibility indexes"""

    app_activity = Keyword()
    transition_type = Keyword()
    prev_ts = Date()
    prev_ts_elapsed_ns = Long()
    interaction_type = Keyword()
    visible_text = Text()
    char_count = Integer()
    web_view_detected = Boolean()
    skipped_nodes = Object(dynamic=True)
    scroll_depth_pct = Float()
    scroll_y = Long()
    max_scroll_y = Long()
    reason = Keyword()
    note = Keyword()
    permission_granted = Boolean()
    browser_text_capture = Boolean()
    total_events = Integer()
    permission_state_at_end = Keyword()
    by_type = Object(dynamic=True)
    events_by_tier = Object(dynamic=True)
    health = Object(dynamic=True)


class MobileAccessibilityAppIndex(MobileAccessibilityIndex):
    """Index for accessibility events of apps that are not browsers"""

    class Index(MobileIndex.Index):
        """Elasticsearch index configuration for accessibility events of apps."""

        name = "mobile_accessibility_app"


class MobileAccessibilityBrowserIndex(MobileAccessibilityIndex):
    """Index for accessibility events of browsers"""

    class Index(MobileIndex.Index):
        """Elasticsearch index configuration for accessibility events of browsers."""

        name = "mobile_accessibility_browser"
