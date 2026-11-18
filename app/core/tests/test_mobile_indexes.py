"""
Tests for the mobile Elasticsearch indexes.
"""

# pylint: disable=protected-access

from datetime import datetime
from typing import Any

from core.indexes.mobile_accessibility_index import (
    MobileAccessibilityAppIndex,
    MobileAccessibilityBrowserIndex,
)
from core.indexes.mobile_vpn_index import (
    MobileVpnAppIndex,
    MobileVpnBrowserIndex,
)
from django.test import SimpleTestCase
from elasticsearch import BadRequestError
from elasticsearch_dsl import connections

INDEXES = {
    MobileAccessibilityAppIndex: "mobile_accessibility_app",
    MobileAccessibilityBrowserIndex: "mobile_accessibility_browser",
    MobileVpnAppIndex: "mobile_vpn_app",
    MobileVpnBrowserIndex: "mobile_vpn_browser",
}

TEST_INDEX = "test_mobile_accessibility_app"


class MobileIndexDefinitionTests(SimpleTestCase):
    """
    Tests for the definition of the mobile indexes.
    """

    def test_monthly_names(self) -> None:
        """
        Tests every index gets the month appended to its base name.
        """
        for index_class, name in INDEXES.items():
            with self.subTest(index=name):
                self.assertEqual(
                    index_class.get_time_based_index_name(datetime(2026, 10, 1)),
                    f"{name}_2026_10",
                )

    def test_settings(self) -> None:
        """
        Tests every index is single node and tuned for heavy writes.
        """
        for index_class, name in INDEXES.items():
            with self.subTest(index=name):
                self.assertEqual(
                    index_class._index.to_dict()["settings"],
                    {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "refresh_interval": "30s",
                        "codec": "best_compression",
                    },
                )

    def test_mapping(self) -> None:
        """
        Tests undeclared fields are rejected and the raw event is not indexed.
        """
        for index_class, name in INDEXES.items():
            with self.subTest(index=name):
                mappings = index_class._index.to_dict()["mappings"]
                self.assertEqual(mappings["dynamic"], "strict")
                self.assertEqual(
                    mappings["properties"]["raw"],
                    {"type": "object", "enabled": False},
                )
                self.assertEqual(
                    mappings["properties"]["ts_elapsed_realtime_nanos"],
                    {"type": "long"},
                )

    def test_module_fields(self) -> None:
        """
        Tests each module only has its own promoted fields.
        """
        accessibility = MobileAccessibilityAppIndex._index.to_dict()["mappings"]
        vpn = MobileVpnAppIndex._index.to_dict()["mappings"]

        self.assertEqual(accessibility["properties"]["visible_text"], {"type": "text"})
        self.assertNotIn("qname", accessibility["properties"])
        self.assertEqual(vpn["properties"]["qname"], {"type": "keyword"})
        self.assertNotIn("visible_text", vpn["properties"])


class MobileIndexElasticsearchTests(SimpleTestCase):
    """
    Tests for the mobile indexes against a running Elasticsearch.
    """

    def setUp(self) -> None:
        self.es_client = connections.get_connection()
        self.es_client.indices.delete(index=TEST_INDEX, ignore_unavailable=True)
        MobileAccessibilityAppIndex._index.clone(name=TEST_INDEX).create()
        self.addCleanup(
            self.es_client.indices.delete, index=TEST_INDEX, ignore_unavailable=True
        )

    def save(self, **fields: Any) -> None:
        """
        Save a document in the test index and make it searchable.
        """
        MobileAccessibilityAppIndex(**fields).save(index=TEST_INDEX, refresh=True)

    def test_raw_event_is_kept_but_not_searchable(self) -> None:
        """
        Tests the raw event comes back as sent while only promoted fields
        can be searched.
        """
        raw = {"app": {"package": "com.a.app"}, "visibleText": "hello world"}
        self.save(user_id="u1", visible_text="hello world", raw=raw)

        found = MobileAccessibilityAppIndex.search(index=TEST_INDEX)
        by_text = found.query("match", visible_text="hello").execute()
        by_raw = found.query("match", **{"raw.app.package": "com.a.app"}).execute()

        self.assertEqual(len(by_text), 1)
        self.assertEqual(by_text[0].raw.to_dict(), raw)
        self.assertEqual(len(by_raw), 0)

    def test_nanosecond_value_is_exact(self) -> None:
        """
        Tests a value above JavaScript's safe integer range is not rounded.
        """
        value = 2**62 + 1
        self.save(ts_elapsed_realtime_nanos=value)

        found = MobileAccessibilityAppIndex.search(index=TEST_INDEX).execute()

        self.assertEqual(found[0].ts_elapsed_realtime_nanos, value)

    def test_counter_objects_accept_their_keys(self) -> None:
        """
        Tests objects with variable keys are stored and searchable.
        """
        self.save(by_type={"visible_text": 3}, skipped_nodes={"node.editable": 1})

        found = MobileAccessibilityAppIndex.search(index=TEST_INDEX)
        by_type = found.query("range", by_type__visible_text={"gte": 1}).execute()
        skipped = found.query("range", skipped_nodes__node__editable={"gte": 1})

        self.assertEqual(len(by_type), 1)
        self.assertEqual(skipped.count(), 1)

    def test_undeclared_field_is_rejected(self) -> None:
        """
        Tests a misspelled field fails instead of being stored unsearchable.
        """
        with self.assertRaises(BadRequestError):
            self.save(user_id="u1", visible_txt="hello")
