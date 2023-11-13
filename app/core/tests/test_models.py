"""
Tests for the models.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase


class ModelTests(TestCase):
    """
    Tests for the models.
    """

    def test_create_user_with_token(self) -> None:
        """
        Tests creating a new user with a token.
        """
        user = get_user_model().objects.create_user()
        self.assertIsInstance(user, get_user_model())
        self.assertTrue(user.token)
        self.assertTrue(user.is_active)

    def test_create_superuser(self) -> None:
        """
        Tests creating a new superuser.
        """
        user = get_user_model().objects.create_superuser()
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_generate_token(self) -> None:
        """
        Tests generating a random token.
        """
        user = get_user_model().objects.create_user()
        self.assertEqual(len(user.token), 32)

    def test_token_is_unique(self) -> None:
        """
        Tests that the token is unique.
        """
        user = get_user_model().objects.create_user()
        user2 = get_user_model().objects.create_user()
        self.assertNotEqual(user.token, user2.token)

    def test_str_method(self) -> None:
        """
        Tests the __str__ method.
        """
        user = get_user_model().objects.create_user()
        self.assertEqual(str(user), user.token)
