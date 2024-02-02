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
        Tests creating a new user with a providen token.
        """
        user_id = "test"
        token_gesis = "test123"
        user = get_user_model().objects.create_user(
            user_id=user_id,
            token_gesis=token_gesis,
        )
        self.assertEqual(user.user_id, user_id)
        self.assertTrue(user.check_password(token_gesis))
        self.assertFalse(user.is_staff)

    def test_new_user_invalid_user_id(self) -> None:
        """
        Tests creating a new user with no user_id raises an error.
        """
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(user_id="", token_gesis="test123")

    def test_create_superuser(self) -> None:
        """
        Tests creating a new superuser.
        """
        user = get_user_model().objects.create_superuser(
            user_id="test", token_gesis="test123"
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    # def test_str_method(self) -> None:
    #     """
    #     Tests the __str__ method.
    #     """
    #     user = get_user_model().objects.create_user(token="test")
    #     self.assertEqual(str(user), user.token)
