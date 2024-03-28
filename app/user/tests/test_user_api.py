"""
Tests for the user API.
"""

from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.db import models
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


def create_user(**params) -> models.Model:
    """
    Helper function to create a user.
    """
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """
    Tests the users API (public).
    """

    def setUp(self) -> None:
        """Creates a client for the tests."""
        self.client = APIClient()

    def test_create_user_success(self) -> None:
        """Tests creating a user without waves payload."""
        payload = {
            "user_id": "test",
            "password": "test123",
            "privacy": {
                "privacy_mode": False,
                "privacy_start_time": datetime.now(timezone.utc).isoformat(),
                "privacy_end_time": datetime.now(timezone.utc).isoformat(),
            },
            "extension": {
                "extension_version": "string",
                "extension_installed_at": datetime.now(timezone.utc).isoformat(),
                "extension_updated_at": datetime.now(timezone.utc).isoformat(),
                "extension_browser": "string",
            },
        }

        response = self.client.post(CREATE_USER_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(user_id=payload["user_id"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", response.data)

    def test_create_user_with_waves_success(self) -> None:
        """Tests creating a user with waves."""
        payload = {
            "user_id": "test",
            "password": "test123",
            "privacy": {
                "privacy_mode": False,
                "privacy_start_time": datetime.now(timezone.utc).isoformat(),
                "privacy_end_time": datetime.now(timezone.utc).isoformat(),
            },
            "extension": {
                "extension_version": "string",
                "extension_installed_at": datetime.now(timezone.utc).isoformat(),
                "extension_updated_at": datetime.now(timezone.utc).isoformat(),
                "extension_browser": "string",
            },
            "waves": [
                {
                    "start_date": datetime.now(timezone.utc).isoformat(),
                    "end_date": datetime.now(timezone.utc).isoformat(),
                    "wave_status": "open",
                    "wave_type": "test",
                    "wave_number": "1",
                    "client_id": "test",
                }
            ],
        }
        response = self.client.post(CREATE_USER_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(user_id=payload["user_id"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", response.data)

        self.assertEqual(len(response.data["waves"]), 1)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(user_id=payload["user_id"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", response.data)

    def test_user_with_email_exists_error(self) -> None:
        """Tests creating a user that already exists fails."""
        payload = {
            "user_id": "test",
            "password": "test123",
        }
        create_user(**payload)

        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self) -> None:
        """Tests that the password must be more than 5 characters."""
        payload = {
            "user_id": "test",
            "password": "pw",
        }
        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = (
            get_user_model().objects.filter(user_id=payload["user_id"]).exists()
        )
        self.assertFalse(user_exists)

    def test_create_token_for_user(self) -> None:
        """Tests that a token is created for the user with valid credentials."""
        payload = {
            "user_id": "test",
            "password": "test123",
        }
        create_user(**payload)
        response = self.client.post(
            TOKEN_URL,
            payload,
        )

        self.assertIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self) -> None:
        """Tests that a token is not created for the user with invalid credentials."""
        create_user(user_id="test", password="test123")
        payload = {
            "user_id": "test",
            "password": "wrong",
        }
        response = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_credentials(self) -> None:
        """Tests that a token is not created for the user with blank credentials."""
        response = self.client.post(TOKEN_URL, {"user_id": "", "password": ""})

        self.assertNotIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self) -> None:
        """Tests that a token is not created for the user with blank password."""
        response = self.client.post(TOKEN_URL, {"user_id": "test", "password": ""})

        self.assertNotIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrive_user_unauthorized(self) -> None:
        """Tests that authentication is required for users."""
        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self) -> None:
        """Creates a client for the tests."""
        self.user = create_user(
            user_id="test",
            password="test123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self) -> None:
        """Tests retrieving profile for logged in used."""
        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "user_id": self.user.user_id,
                "waves": [],
                "privacy": None,
                "extension": None,
            },
        )

    def test_update_user_profile(self) -> None:
        """Tests updating the profile for authenticated user."""
        payload = {
            "password": "newpassword",
        }

        response = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_user_with_wave_authenticated_fails(self) -> None:
        """Tests creating a user with waves."""
        payload = {
            "user_id": "test",
            "password": "test123",
            "waves": [
                {
                    "start_date": datetime.now(timezone.utc),
                    "end_date": datetime.now(timezone.utc),
                    "wave_status": "open",
                    "wave_type": "test",
                    "wave_number": "1",
                    "client_id": "test",
                }
            ],
        }
        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
