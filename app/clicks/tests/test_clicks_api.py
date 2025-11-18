"""
Tests for the clicks API
"""

from core.models import Click
from core.tests.helpers import create_click, create_user, detail_url
from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet
from django.urls import reverse
from domain.serializers import ClickSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase

CLICK_URL: str = reverse("click:click-list")


class PublicClickApiTests(APITestCase):
    """
    Test the pubicly available click API
    """

    def setUp(self) -> None:
        self.client: APIClient = APIClient()

    def test_login_required(self) -> None:
        """
        Test that login is required for retrieving clicks
        """
        # Make a request to the click URL without logging in.
        res: Response = self.client.get(CLICK_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateClickApiTests(APITestCase):
    """
    Test the private click API
    """

    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.user: AbstractUser = create_user(user_id="test", password="testpass")
        self.client.force_authenticate(self.user)

    def test_retrieve_clicks(self) -> None:
        """
        Test retrieving a list of clicks
        """
        create_click(user=self.user)
        create_click(user=self.user)

        res: Response = self.client.get(CLICK_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        clicks: QuerySet[Click] = Click.objects.all()

        # Serialize the clicks.
        serializer: ClickSerializer = ClickSerializer(clicks, many=True)

        self.assertEqual(len(res.data["results"]), len(clicks))

        response_ids = [item["id"] for item in res.data["results"]]
        serializer_ids = [item["id"] for item in serializer.data]
        self.assertEqual(response_ids, serializer_ids)

    def test_clicks_limited_to_user(self) -> None:
        """
        Test that clicks for the authenticated user are returned
        """
        user2: AbstractUser = create_user(user_id="other", password="testpass")
        create_click(user=user2)

        click: Click = create_click(user=self.user)

        res: Response = self.client.get(CLICK_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["click_type"], click.click_type)

    def test_update_click(self) -> None:
        """
        Test updating a click
        """
        click: Click = create_click(user=self.user)
        url: str = detail_url("click", click.id)

        payload: dict = {"click_target_element": "a", "click_target_tag": "a"}

        self.client.patch(url, payload)
        click.refresh_from_db()
        self.assertEqual(click.click_target_tag, payload["click_target_tag"])
        self.assertEqual(click.click_target_element, payload["click_target_element"])

    def test_delete_click(self) -> None:
        """
        Test deleting a click
        """
        click: Click = create_click(user=self.user)
        url: str = detail_url("click", click.id)
        self.client.delete(url)

        clicks: QuerySet[Click] = Click.objects.all()
        self.assertEqual(len(clicks), 0)
