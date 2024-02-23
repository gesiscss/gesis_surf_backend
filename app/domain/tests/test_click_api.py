"""
Tests for the clicks API
"""

from core.models import Click, User
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from domain.serializers import ClickSerializer
from rest_framework import status
from rest_framework.test import APIClient

DOMAIN_URL = reverse("tab:click-list")


def detail_url(click: Click) -> str:
    """
    Return the click detail URL
    """
    return reverse("tab:click-detail", args=[click.id])


def create_user(username: str = "test", password: str = "testpass") -> User:
    """
    Create and return a sample user
    """
    return get_user_model().objects.create_user(username, password)


def create_click(user: User, **params: dict) -> Click:
    """
    Create and return a sample click
    """
    defaults = {
        "click_location": "test",
        "click_type": "click",
        "click_time": "2024-06-01 17:00:00",
    }
    defaults.update(params)
    return Click.objects.create(user=user, **defaults)


class PublicClickApiTests(TestCase):
    """
    Test the pubicly available click API
    """

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self) -> None:
        """
        Test that login is required for retrieving clicks
        """
        # Make a request to the click URL without logging in.
        res = self.client.get(DOMAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# class PrivateClickApiTests(TestCase):
#     """
#     Test the private click API
#     """

#     def setUp(self) -> None:
#         self.client = APIClient()
#         self.user = create_user()
#         self.client.force_authenticate(self.user)

#     def test_retrieve_clicks(self) -> None:
#         """
#         Test retrieving a list of clicks
#         """
#         create_click(user=self.user)
#         create_click(user=self.user)

#         res = self.client.get(DOMAIN_URL)
#         clicks = Click.objects.all().order_by("-id")
#         # Serialize the clicks.
#         serializer = ClickSerializer(clicks, many=True)

#         self.assertEqual(res.status_code, status.HTTP_200_OK)
#         self.assertEqual(res.data, serializer.data)

#     def test_clicks_limited_to_user(self) -> None:
#         """
#         Test that clicks for the authenticated user are returned
#         """
#         user2 = create_user(username="other", password="testpass")
#         create_click(user=user2)
#         click = create_click(user=self.user)

#         res = self.client.get(DOMAIN_URL)
#         self.assertEqual(res.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(res.data), 1)
#         self.assertEqual(res.data[0]["click_location"], click.click_location)
