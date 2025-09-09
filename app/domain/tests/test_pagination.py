"""
Django Rest Framework Pagination Test
"""

from core.tests.helpers import create_domain, create_user
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

DOMAIN_URL = reverse("domain:domain-list")


class PublicPaginationTestCase(TestCase):
    """
    Test Pagination
    """

    def setUp(self) -> None:
        """
        Setup the test
        """
        self.client = APIClient()

    def test_login_required(self) -> None:
        """
        Test that login is required for retrieving domains
        """
        res = self.client.get(DOMAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatePaginationTest(APITestCase):
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

    def test_retrive_paginated_domains(self) -> None:
        """
        Test retrieving paginated domains
        """
        for _ in range(20):
            create_domain(user=self.user)

        res = self.client.get(DOMAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 10)

    def test_custom_page_size(self) -> None:
        """
        Test custom page size
        """
        for _ in range(20):
            create_domain(user=self.user)

        res = self.client.get(DOMAIN_URL, {"page_size": 5})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 5)

    def test_max_page_size(self) -> None:
        """
        Test max page size
        """
        for _ in range(50):
            create_domain(user=self.user)

        res = self.client.get(DOMAIN_URL, {"page_size": 100})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 50)

    def test_pagination_links(self) -> None:
        """
        Test pagination links
        """
        for _ in range(20):
            create_domain(user=self.user)

        res = self.client.get(DOMAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data["links"]["next"], "http://testserver/api/domain/domains/?page=2"
        )
        self.assertEqual(res.data["links"]["previous"], None)

    def test_page_navigation(self) -> None:
        """
        Test page navigation
        """
        for _ in range(20):
            create_domain(user=self.user)

        res = self.client.get(DOMAIN_URL, {"page": 2})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 10)
        self.assertEqual(res.data["links"]["next"], None)
        self.assertEqual(
            res.data["links"]["previous"], "http://testserver/api/domain/domains/"
        )

    def test_invalid_page(self) -> None:
        """
        Test invalid page
        """
        for _ in range(20):
            create_domain(user=self.user)

        res = self.client.get(DOMAIN_URL, {"page": 3333})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
