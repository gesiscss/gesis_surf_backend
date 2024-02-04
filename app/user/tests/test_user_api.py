"""
Tests for the user API.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user:create")


def create_user(**params) -> get_user_model():
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
        """Tests creating a user with valid payload is successful."""
        payload = {
            "user_id": "test",
            "password": "test123",
        }
        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**response.data)
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

    # def test_create_token_for_user(self) -> None:
    #     """Tests that a token is created for the user."""
    #     payload = {
    #         "user_id": "test",
    #         "password": "test123",
    #     }
    #     create_user(**payload)
    #     response = self.client.post(
    #         reverse("user:token"),
    #         payload,
    #     )

    #     self.assertIn("token", response.data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
