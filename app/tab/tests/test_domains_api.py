"""
Tests for the domains API.
"""

from datetime import datetime
from typing import Any

from core.models import Domain
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from tab.serializers import DomainSerializer

DOMAIN_URL = reverse("tab:domain-list")


def detail_url(domain_id: int) -> str:
    """
    Return domain detail URL
    """
    return reverse("tab:domain-detail", args=[domain_id])


def create_user(username: str = "test", password: str = "testpass"):
    """
    Create and return a sample user
    """
    return get_user_model().objects.create_user(username, password)


def create_domain(user, **params) -> Domain:
    """
    Create and return a sample domain
    """
    defaults = {
        "domain_title": "test.com",
        "domain_url": "https://test.com",
        "domain_fav_icon": "https://test.com/favicon.ico",
        "domain_status": "active",
        "start_time": datetime.strptime("2021-06-01 08:00:00", "%Y-%m-%d %H:%M:%S"),
        "closing_time": datetime.strptime("2021-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
        "snapshot_html": "<html>Test</html>",
    }
    defaults.update(params)
    return Domain.objects.create(user=user, **defaults)


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


class PrivateDomainApiTests(TestCase):
    """
    Test the authorized user domain API
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_domains(self) -> None:
        """
        Test retrieving a list of domains
        """
        create_domain(user=self.user)
        create_domain(user=self.user)

        res = self.client.get(DOMAIN_URL)

        domains = Domain.objects.all().order_by("created_at")
        # Serializing the domains and getting all the objects
        serializer = DomainSerializer(domains, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_domains_limited_to_user(self) -> None:
        """
        Test that domains for the authenticated user are returned
        """
        user2 = create_user(username="test2", password="testpass")
        create_domain(user=user2)
        domain = create_domain(user=self.user)

        res = self.client.get(DOMAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["domain_title"], domain.domain_title)

    def test_update_domain(self) -> None:
        """
        Test updating a domain
        """
        domain: str = create_domain(user=self.user)
        payload: dict[str, Any] = {
            "domain_title": "test.com",
            "domain_status": "inactive",
        }
        url: str = detail_url(domain.id)

        self.client.patch(url, payload)
        domain.refresh_from_db()
        self.assertEqual(domain.domain_status, payload["domain_status"])

    def test_delete_tag(self) -> None:
        """
        Test deleting a domain
        """
        domain = create_domain(user=self.user)

        url = detail_url(domain.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        domains = Domain.objects.filter(user=self.user)
        self.assertFalse(domains.exists())
