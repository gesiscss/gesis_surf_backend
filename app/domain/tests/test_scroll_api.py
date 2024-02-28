"""
Test for the scroll API
"""

from core.models import Domain, Scroll, User
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from domain.serializers import ScrollSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

SCROLL_URL: str = reverse("domain:scroll-list")


def create_domain(user: User, **params: dict) -> Domain:
    """
    Create and return a sample domain
    """
    defaults: dict = {
        "domain_title": "test.com",
        "domain_url": "https://test.com",
        "domain_fav_icon": "https://test.com/favicon.ico",
        "domain_status": "active",
    }
    defaults.update(params)
    return Domain.objects.create(user=user, **defaults)


def create_scroll(user: User, **params: dict) -> Scroll:
    """
    Create and return a sample scroll
    """
    defaults: dict = {
        "scroll_x": "0",
        "scroll_y": "0",
        "page_x_offset": "0",
        "page_y_offset": "0",
        "scroll_time": "2024-06-01 17:00:00",
        "domain": create_domain(user=user),
    }
    defaults.update(params)
    return Scroll.objects.create(user=user, **defaults)


class PublicScrollApiTests(TestCase):
    """
    Test the publicly available scroll API
    """

    def setUp(self):
        self.client: APIClient = APIClient()

    def test_login_required(self) -> None:
        """
        Test that login is required for retrieving scrolls
        """
        res: Response = self.client.get(SCROLL_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateScrollApiTests(TestCase):
    """
    Test the private scroll API
    """

    def setUp(self):
        self.client: APIClient = APIClient()
        self.user: User = get_user_model().objects.create_user("test", "testpass")
        self.client.force_authenticate(self.user)

    def test_retrieve_scrolls(self) -> None:
        """
        Test retrive scrolls for authenticated user
        """
        create_scroll(user=self.user)
        create_scroll(user=self.user)

        res: Response = self.client.get(SCROLL_URL)

        scrolls: Scroll = Scroll.objects.all().order_by("-id")
        # Serialize the scrolls
        serializer: ScrollSerializer = ScrollSerializer(scrolls, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
