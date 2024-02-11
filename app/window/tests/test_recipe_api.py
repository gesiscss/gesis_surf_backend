"""
Tests for the recipe API
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient
from core.models import Window

from recipe.serializers import WindowSerializer

WINDOW_URL = reverse("window:window-list")

def create_window(user, **params):
    """
    Create and return a sample window
    """
    defaults = {
        "start_time": "2021-06-01 08:00:00",
        "closing_time": "2021-06-01 17:00:00",
        "created_at": "2021-06-01 08:00:00",
    }
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
        self.user = get_user_model().objects.create_user("testuser", "testpass")
        self.client.force_authenticate(self.user)

    def test_retrieve_windows(self):
        """
        Test retrieving a list of windows
        """
        create_window(user=self.user)
        create_window(user=self.user)

        res = self.client.get(WINDOW_URL)

        windows = Window.objects.all().order_by("-id")
        serializer = WindowSerializer(windows, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
