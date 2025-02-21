""" Test the user API (super user). """

from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import User

CREATE_USER_URL = reverse("user:create")


def create_super_user(**params) -> User:
    """
    Create a super user.
    """
    return get_user_model().objects.create_superuser(**params)


class SuperuserUserApiTests(TestCase):
    """
    Test the user API (super user).
    """

    def setUp(self) -> None:  # pylint: disable=invalid-name
        """Set up the test."""
        self.client = APIClient()
        self.super_user = create_super_user(
            user_id="superuser",
            password="superuserpass",
        )
        self.client.force_authenticate(self.super_user)

    def test_create_user_as_superuser(self) -> None:
        """
        Test creating a new user as a super user.
        """
        payload = {
            "user_id": "testuser",
            "password": "testpass",
            "privacy": {
                "privacy_mode": False,
                "privacy_start_time": datetime.now(timezone.utc).isoformat(),
                "privacy_end_time": datetime.now(timezone.utc).isoformat(),
            },
            "extension": {
                "extension_version": "1.0.0",
                "extension_installed_at": datetime.now(timezone.utc).isoformat(),
                "extension_updated_at": datetime.now(timezone.utc).isoformat(),
                "extension_browser": "Chrome",
            },
        }
        response = self.client.post(CREATE_USER_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_user_as_superuser_invalid(self) -> None:
        """
        Test creating a new user as a super user with invalid payload.
        """
        payload = {
            "user_id": "",
            "password": "",
            "privacy": {
                "privacy_mode": False,
                "privacy_start_time": datetime.now(timezone.utc).isoformat(),
                "privacy_end_time": datetime.now(timezone.utc).isoformat(),
            },
            "extension": {
                "extension_version": "1.0.0",
                "extension_installed_at": datetime.now(timezone.utc).isoformat(),
                "extension_updated_at": datetime.now(timezone.utc).isoformat(),
                "extension_browser": "Chrome",
            },
        }
        response = self.client.post(CREATE_USER_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_as_no_superuser(self) -> None:
        """
        Test creating a new user as a non-super user.
        """
        user = get_user_model().objects.create_user(
            user_id="testuser",
            password="testpass",
        )
        self.client.force_authenticate(user)
        payload = {
            "user_id": "testuser",
            "password": "testpass",
            "privacy": {
                "privacy_mode": False,
                "privacy_start_time": datetime.now(timezone.utc).isoformat(),
                "privacy_end_time": datetime.now(timezone.utc).isoformat(),
            },
            "extension": {
                "extension_version": "1.0.0",
                "extension_installed_at": datetime.now(timezone.utc).isoformat(),
                "extension_updated_at": datetime.now(timezone.utc).isoformat(),
                "extension_browser": "Chrome",
            },
        }
        response = self.client.post(CREATE_USER_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
