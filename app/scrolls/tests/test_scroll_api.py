"""
Test for the scroll API
"""

from core.models import Domain, Scroll, User
from core.tests.helpers import create_scroll, create_user, detail_url
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from domain.serializers import ScrollSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase

SCROLL_URL: str = reverse("scroll:scroll-list")


class PublicScrollApiTests(APITestCase):
    """
    Test the publicly available scroll API.
    """

    def setUp(self):
        """
        Set up the test client.
        """
        self.client: APIClient = APIClient()

    def test_login_required(self) -> None:
        """
        Test that login is required for retrieving scrolls
        """
        res: Response = self.client.get(SCROLL_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateScrollApiTests(APITestCase):
    """
    Test the private scroll API.
    """

    def setUp(self):
        self.client: APIClient = APIClient()
        self.user: AbstractUser = create_user(user_id="test", password="testpass")
        self.client.force_authenticate(self.user)

    def test_retrieve_scrolls(self) -> None:
        """
        Test retrive scrolls for authenticated user
        """
        create_scroll(user=self.user)
        create_scroll(user=self.user)

        res: Response = self.client.get(SCROLL_URL)

        scrolls: Scroll = Scroll.objects.all().order_by("-created_at")
        # Serialize the scrolls
        serializer: ScrollSerializer = ScrollSerializer(scrolls, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_scroll_limited_user(self) -> None:
        """
        Test scrolls for authenticated user.
        """
        user2: User = create_user(username="other", password="testpass")
        create_scroll(user=user2)
        scroll: Scroll = create_scroll(user=self.user)

        res: Response = self.client.get(SCROLL_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["scroll_x"], scroll.scroll_x)

    def test_update_scroll(self) -> None:
        """
        Test updating a scroll
        """
        scroll: Scroll = create_scroll(user=self.user)
        url: str = detail_url(scroll)
        payload: dict = {
            "scroll_x": 100,
            "scroll_y": 100,
            "page_x_offset": 100,
            "page_y_offset": 100,
            "scroll_time": "2024-06-01 17:00:00",
        }
        self.client.patch(url, payload)

        scroll.refresh_from_db()
        self.assertEqual(scroll.scroll_x, payload["scroll_x"])

    def test_delete_scroll(self) -> None:
        """
        Test deleting a scroll
        """
        scroll: Scroll = create_scroll(user=self.user)
        url: str = detail_url(scroll)

        response: Response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        scrolls: Scroll = Scroll.objects.filter(user=self.user)
        self.assertEqual(scrolls.exists(), False)
