"""
Tests for the domains API.
"""

from typing import Any

from core.models import Domain
from core.tests.helpers import create_domain, create_user, detail_url
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from tab.serializers import DomainSerializer

DOMAIN_URL = reverse("tab:domain-list")


class PublicDomainApiTests(APITestCase):
    """
    Test the publicly available domain API
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
    Test the authorized user domain API
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(user_id="test", password="testpass")
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
        user2 = create_user(user_id="test2", password="testpass")
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
        domain: Domain = create_domain(user=self.user)
        payload: dict[str, Any] = {
            "domain_title": "test.com",
        }
        url: str = detail_url("domain", domain.id)

        self.client.patch(url, payload)
        domain.refresh_from_db()
        self.assertEqual(domain.domain_title, payload["domain_title"])

    def test_delete_tag(self) -> None:
        """
        Test deleting a domain
        """
        domain = create_domain(user=self.user)

        url = detail_url("domain", domain.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        domains = Domain.objects.filter(user=self.user)
        self.assertFalse(domains.exists())
