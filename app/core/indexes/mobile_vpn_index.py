"""
Indexes that work with mobile VPN events
"""

from elasticsearch_dsl import Date, Integer, Ip, Keyword, Long

from .mobile_index import MobileIndex


class MobileVpnIndex(MobileIndex):
    """Fields shared by the mobile VPN indexes"""

    flow_id = Keyword()
    protocol = Keyword()
    dst_host = Keyword()
    dst_port = Integer()
    flow_created_at = Date()
    flow_created_at_elapsed_ns = Long()
    flow_last_seen = Date()
    flow_last_seen_elapsed_ns = Long()
    bytes_out = Long()
    bytes_in = Long()
    end_reason = Keyword()
    app_attribution_status = Keyword()
    domain_source = Keyword()
    server_name = Keyword()
    server_ip = Ip()
    server_port = Integer()
    qname = Keyword()
    rtt_ms = Integer()


class MobileVpnAppIndex(MobileVpnIndex):
    """Index for VPN events of apps that are not browsers"""

    class Index(MobileIndex.Index):
        """Elasticsearch index configuration for VPN events of apps."""

        name = "mobile_vpn_app"


class MobileVpnBrowserIndex(MobileVpnIndex):
    """Index for VPN events of browsers"""

    class Index(MobileIndex.Index):
        """Elasticsearch index configuration for VPN events of browsers."""

        name = "mobile_vpn_browser"
