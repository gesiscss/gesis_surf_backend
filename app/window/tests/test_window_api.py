"""
Tests for the recipe API
"""

from datetime import datetime, timezone

from core.models import Window
from core.tests.helpers import (
    create_global_session,
    create_user,
    create_window,
    detail_url,
)
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from window.serializers import WindowDetailSerializer, WindowSerializer

WINDOW_URL = reverse("window:window-list")


class PublicWindowApiTests(APITestCase):
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


class PrivateWindowApiTests(APITestCase):
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
        # Create 3 windows & global session
        global_session = create_global_session(user=self.user)

        # Attach global session to window
        create_window(user=self.user, global_session=global_session)
        create_window(user=self.user, global_session=global_session)
        create_window(user=self.user, global_session=global_session)

        res = self.client.get(WINDOW_URL)

        # The latest window should be the first in the list
        windows = Window.objects.all().order_by("-created_at")
        # Compare the response data with the serialized data
        serializer = WindowSerializer(windows, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_windows_limited_to_user(self):
        """
        Test retrieving windows for authenticated user OWASP security
        """
        user2 = create_user(user_id="test2", password="testpass")
        global_session = create_global_session(user=user2)

        create_window(user=user2, global_session=global_session)
        create_window(user=self.user, global_session=global_session)

        res = self.client.get(WINDOW_URL)

        windows = Window.objects.filter(user=self.user)
        serializer = WindowSerializer(windows, many=True)

        # Compare the response data with the serialized data
        self.assertEqual(res.data["results"], serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_get_window_detail(self):
        """
        Test viewing a window detail
        """
        # Create Global Session
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)

        # The URL to the detail of the window
        url = detail_url("window", window.id)
        res = self.client.get(url)

        serializer = WindowDetailSerializer(window)
        self.assertEqual(res.data, serializer.data)

    def test_create_window(self):
        """
        Test creating a window
        """
        # Create Global Session
        global_session = create_global_session(user=self.user)

        payload = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "window_num": 1,
            "window_session_id": "session_12345",
            "global_session": str(global_session.id),
        }

        res = self.client.post(WINDOW_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        window = Window.objects.get(id=res.data["id"])

        for key, value in payload.items():
            if key == "global_session":
                self.assertEqual(window.global_session.id, global_session.id)
            else:
                self.assertEqual(getattr(window, key), value)
        self.assertEqual(window.user, self.user)

    def test_partial_update_window(self):
        """
        Test updating a window with patch
        """
        # Create Global Session
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)

        payload = {"start_time": datetime.now(timezone.utc)}
        url = detail_url("window", window.id)

        self.client.patch(url, payload)

        window.refresh_from_db()
        self.assertEqual(window.start_time, payload["start_time"])

    def test_full_update_window(self):
        """
        Test updating a window with put
        """

        # Create Global Session
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)

        payload = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "window_num": 1,
            "window_session_id": "session_12345",
            "global_session": str(global_session.id),
        }
        url = detail_url("window", window.id)
        self.client.put(url, payload)

        window.refresh_from_db()
        self.assertEqual(window.start_time, payload["start_time"])

    def user_returns_error(self):
        """
        Test that the user cannot be updated from window detail
        """
        new_user = create_user(user_id="new_user", password="new_user")
        global_session = create_global_session(user=new_user)
        window = create_window(user=self.user, global_session=global_session)

        payload = {"user": new_user}
        url = detail_url("window", window.id)
        self.client.patch(url, payload)

        window.refresh_from_db()
        self.assertEqual(window.user, self.user)

    def test_delete_window(self):
        """
        Test deleting window successful
        """
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)
        url = detail_url("window", window.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Window.objects.filter(id=window.id).exists(), False)

    def test_delete_other_user_recipe_error(self):
        """
        Test that a user cannot delete another user's window
        """
        user2 = create_user(user_id="test2", password="testpass")

        global_session = create_global_session(user=user2)
        window = create_window(user=user2, global_session=global_session)

        url = detail_url("window", window.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Window.objects.filter(id=window.id).exists(), True)
