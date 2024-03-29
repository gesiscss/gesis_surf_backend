"""
Tests for the clicks API
"""

from datetime import datetime

from core.models import Click, Domain, User
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from domain.serializers import ClickSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

CLICK_URL: str = reverse("domain:click-list")


def detail_url(click: Click) -> str:
    """
    Return the click detail URL
    """
    return reverse("domain:click-detail", args=[click.id])


def create_user(username: str = "test", password: str = "testpass") -> User:
    """
    Create and return a sample user
    """
    return get_user_model().objects.create_user(username, password)


def create_domain(user: User, **params: dict) -> Domain:
    """
    Create and return a sample domain
    """
    defaults: dict = {
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


def create_click(user: User, **params: dict) -> Click:
    """
    Create and return a sample click
    """
    defaults: dict = {
        "click_time": "2021-06-01T08:00:00Z",
        "click_type": "click",
        "click_target_element": "button",
        "click_target_tag": "button",
        "click_target_id": "btn-1",
        "click_target_class": "btn",
        "click_page_x": 100.0,
        "click_page_y": 200.0,
        "click_referrer": "https://test.com",
        "domain": create_domain(user=user),
    }
    defaults.update(params)
    return Click.objects.create(user=user, **defaults)


class PublicClickApiTests(TestCase):
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


class PrivateClickApiTests(TestCase):
    """
    Test the private click API
    """

    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.user: User = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_clicks(self) -> None:
        """
        Test retrieving a list of clicks
        """
        create_click(user=self.user)
        create_click(user=self.user)

        res: Response = self.client.get(CLICK_URL)

        clicks: Click = Click.objects.all().order_by("-created_at")
        # Serialize the clicks.
        serializer: ClickSerializer = ClickSerializer(clicks, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_clicks_limited_to_user(self) -> None:
        """
        Test that clicks for the authenticated user are returned
        """
        user2: User = create_user(username="other", password="testpass")
        create_click(user=user2)
        click: Click = create_click(user=self.user)

        res: Response = self.client.get(CLICK_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["click_type"], click.click_type)
        self.assertEqual(res.data[0]["click_time"], click.click_time)

    def test_update_cick(self) -> None:
        """
        Test updating a click
        """
        click: Click = create_click(user=self.user)
        url: str = detail_url(click)
        payload: dict = {"click_target_element": "a", "click_target_tag": "a"}
        self.client.patch(url, payload)

        click.refresh_from_db()
        self.assertEqual(click.click_target_element, payload["click_target_element"])

    def test_delete_click(self) -> None:
        """
        Test deleting a click
        """
        click: Click = create_click(user=self.user)
        url: str = detail_url(click)
        self.client.delete(url)

        clicks: Click = Click.objects.all()
        self.assertEqual(len(clicks), 0)
