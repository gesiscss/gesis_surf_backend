"""
Test for the scroll API
"""

from core.models import Scroll
from core.tests.helpers import create_scroll, create_user
from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet
from django.urls import reverse
from domain.serializers import ScrollSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase

SCROLL_URL: str = reverse("scrolls:scroll-list")


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
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        scrolls: QuerySet[Scroll] = Scroll.objects.all()

        # Serialize the scrolls
        serializer: ScrollSerializer = ScrollSerializer(scrolls, many=True)
        self.assertEqual(len(res.data["results"]), len(serializer.data))

        response_ids = [item["id"] for item in res.data["results"]]
        serializer_ids = [item["id"] for item in serializer.data]
        self.assertEqual(response_ids, serializer_ids)

    def test_scroll_limited_user(self) -> None:
        """
        Test scrolls for authenticated user.
        """
        user2: AbstractUser = create_user(user_id="other", password="testpass")
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
        url: str = reverse("scrolls:scroll-detail", args=[scroll.id])
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
        # url: str = detail_url("scroll", scroll.id)
        url: str = reverse("scrolls:scroll-detail", args=[scroll.id])

        response: Response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        scrolls: QuerySet[Scroll] = Scroll.objects.filter(user=self.user)
        self.assertEqual(scrolls.exists(), False)
