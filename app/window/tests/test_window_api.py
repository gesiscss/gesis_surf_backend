"""
Tests for the recipe API
"""

import random
from datetime import datetime, timezone

from core.models import Window
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from window.serializers import WindowDetailSerializer, WindowSerializer

WINDOW_URL = reverse("window:window-list")


# Functions outside class do not need logic.
def create_user(**params):
    """
    Create and return a sample user
    """
    return get_user_model().objects.create_user(**params)


def round_datetime(d_t: datetime) -> datetime:
    """
    Round the datetime to the nearest second.
    """
    return d_t.replace(second=0, microsecond=0)


def detail_url(window_id) -> str:
    """
    Create and return a window detail URL
    """
    return reverse("window:window-detail", args=[window_id])


def create_window(user, **params):
    """
    Create and return a sample window
    """
    defaults = {
        "start_time": datetime.now(timezone.utc),
        "closing_time": datetime.strptime("2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
        "window_num": random.randint(1, 100),
    }
    # Update the defaults with the params provided in the function.
    defaults.update(params)
    return Window.objects.create(user=user, **defaults)


class PublicWindowApiTests(TestCase):
    """
    Test unauthenticated window API access
    """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """
        Test that authentication is required
        """
        res = self.client.get(WINDOW_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateWindowApiTests(TestCase):
    """
    Test authenticated window API access
    """

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(user_id="test", password="testpass")
        self.client.force_authenticate(self.user)

    def test_auth_required(self):
        """
        Test that authentication is required
        """
        res = self.client.get(WINDOW_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrive_windows(self):
        """
        Test retrieving a list of windows by created_at
        """
        # Create 3 windows
        create_window(user=self.user)
        create_window(user=self.user)
        create_window(user=self.user)

        res = self.client.get(WINDOW_URL)

        # The latest window should be the first in the list
        windows = Window.objects.all().order_by("-created_at")
        # Compare the response data with the serialized data
        serializer = WindowSerializer(windows, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_windows_limited_to_user(self):
        """
        Test retrieving windows for authenticated user OWASP security
        """
        user2 = create_user(user_id="test2", password="testpass")

        create_window(user=user2)
        create_window(user=self.user)

        res = self.client.get(WINDOW_URL)

        windows = Window.objects.filter(user=self.user)
        serializer = WindowSerializer(windows, many=True)

        # Compare the response data with the serialized data
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_get_window_detail(self):
        """
        Test viewing a window detail
        """
        window = create_window(user=self.user)
        # The URL to the detail of the window
        url = detail_url(window.id)
        res = self.client.get(url)

        serializer = WindowDetailSerializer(window)
        self.assertEqual(res.data, serializer.data)

    def test_create_window(self):
        """
        Test creating a window
        """
        payload = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "window_num": "1",
        }

        res = self.client.post(WINDOW_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        window = Window.objects.get(id=res.data["id"])

        for key, value in payload.items():
            self.assertEqual(getattr(window, key), value)
        self.assertEqual(window.user, self.user)

    def test_partial_update_window(self):
        """
        Test updating a window with patch
        """
        window = create_window(user=self.user)
        payload = {"start_time": datetime.now(timezone.utc)}
        url = detail_url(window.id)
        self.client.patch(url, payload)
        window.refresh_from_db()
        self.assertEqual(window.start_time, payload["start_time"])

    def test_full_update_window(self):
        """
        Test updating a window with put
        """
        window = create_window(user=self.user)
        payload = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "window_num": "1",
        }
        url = detail_url(window.id)
        self.client.put(url, payload)
        window.refresh_from_db()
        self.assertEqual(window.start_time, payload["start_time"])

    def user_returns_error(self):
        """
        Test that the user cannot be updated from window detail
        """
        new_user = create_user(user_id="new_user", password="new_user")
        window = create_window(user=self.user)

        payload = {"user": new_user}
        url = detail_url(window.id)
        self.client.patch(url, payload)

        window.refresh_from_db()
        self.assertEqual(window.user, self.user)

    def test_delete_window(self):
        """
        Test deleting window succesful
        """
        window = create_window(user=self.user)
        url = detail_url(window.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Window.objects.filter(id=window.id).exists(), False)

    def test_delete_other_user_recipe_error(self):
        """
        Test that a user cannot delete another user's window
        """
        user2 = create_user(user_id="test2", password="testpass")
        window = create_window(user=user2)

        url = detail_url(window.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Window.objects.filter(id=window.id).exists(), True)
