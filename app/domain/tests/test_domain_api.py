"""
Test for Domain APIs.
"""

from datetime import datetime, timezone

from core.models import Click, Domain, Scroll
from core.tests.helpers import (
    create_user,
    create_global_session,
    create_window,
    create_tab,
    create_domain,
    detail_url,
)
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from domain.serializers import DomainSingleSerializer
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

DOMAIN_URL = reverse("domain:domain-list")
SCROLL_URL: str = reverse("domain:scroll-list")


class PublicDomainApiTests(TestCase):
    """
    Test the publicly available domian API
    """

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self) -> None:
        """
        Test that login is required for retrieving domains
        """
        res = self.client.get(DOMAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateDomainApiTests(APITestCase):
    """
    Test authenticated Domain API access
    """

    def setUp(self) -> None:
        """
        Setup the authenticated user
        """
        self.client = APIClient()
        self.user = create_user(user_id="test", password="test123")
        self.client.force_authenticate(self.user)

    def test_retrieve_domains(self) -> None:
        """
        Test retrieving domains
        """
        create_domain(user=self.user)
        create_domain(user=self.user)
        create_domain(user=self.user)

        res = self.client.get(DOMAIN_URL)
        domains = Domain.objects.all().order_by("-created_at")
        serializer = DomainSingleSerializer(domains, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_domains_limited_to_user(self) -> None:
        """
        Test that domains for the authenticated user are returned
        """
        user2 = create_user(user_id="other", password="test123")
        
        create_domain(user=user2)
        domain = create_domain(user=self.user)

        res = self.client.get(DOMAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["domain_title"], domain.domain_title)

    def test_get_domain_detail(self) -> None:
        """
        Test retrieving a domain detail
        """
        domain = create_domain(user=self.user)
        url = detail_url("domain", domain.id)
        res = self.client.get(url)
        serializer = DomainSingleSerializer(domain)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_domain(self) -> None:
        """
        Test creating domain
        """
        payload = {
            "domain_title": "test.com",
            "domain_url": "https://test.com",
            "domain_fav_icon": "https://test.com/favicon.ico",
            "domain_last_accessed": "active",
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "snapshot_html": "<html>Test</html>",
            "domain_session_id": "session123",
        }
        res = self.client.post(DOMAIN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        domain = Domain.objects.get(id=res.data["id"])
        for key, value in payload.items():
            self.assertEqual(value, getattr(domain, key))

    def test_partial_update_domain(self) -> None:
        """
        Test updating a domain with patch
        """
        domain = create_domain(user=self.user)
        payload = {"domain_title": "test.com", "domain_last_accessed": "inactive"}
        url = detail_url("domain", domain.id)
        self.client.patch(url, payload)

        domain.refresh_from_db()
        self.assertEqual(domain.domain_last_accessed, payload["domain_last_accessed"])

    def test_full_update_domain(self) -> None:
        """
        Test updating a domain with put
        """
        domain = create_domain(user=self.user)
        payload = {
            "domain_title": "test.com",
            "domain_url": "https://test.com",
            "domain_fav_icon": "https://test.com/favicon.ico",
            "domain_last_accessed": "inactive",
            "start_time": datetime.strptime("2021-06-01 08:00:00", "%Y-%m-%d %H:%M:%S"),
            "closing_time": datetime.strptime(
                "2021-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
            ),
            "snapshot_html": "<html>Test</html>",
        }
        url = detail_url("domain", domain.id)
        self.client.put(url, payload)
        domain.refresh_from_db()
        self.assertEqual(domain.domain_title, payload["domain_title"])

    def test_user_returns_error(self) -> None:
        """
        Test that the user cannot be updated from domain detail.
        """
        new_user = create_user(user_id="new", password="newpass")
        domain = create_domain(user=self.user)
        payload = {"user": new_user}
        url = detail_url("domain", domain.id)
        self.client.put(url, payload)

        domain.refresh_from_db()
        self.assertNotEqual(domain.user, new_user)

    def test_delete_domain(self) -> None:
        """
        Test deleting a domain
        """
        domain = create_domain(user=self.user)
        url = detail_url("domain", domain.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Domain.objects.count(), 0)
        
    def test_retrieve_html_snapshot(self) -> None:
        """
        Test retrieving the HTML snapshot for a domain
        """
        domain = create_domain(user=self.user, snapshot_html="<html>Test Snapshot</html>")
        url = detail_url("domain", domain.id)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["snapshot_html"], domain.snapshot_html)