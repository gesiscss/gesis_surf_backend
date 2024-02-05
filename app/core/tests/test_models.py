"""
Tests for the models.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from core import models


class ModelTests(TestCase):
    """
    Tests for the models.
    """

    def test_create_user_with_password(self) -> None:
        """
        Tests creating a new user with a providen token.
        """
        user_id = "test"
        password = "test123"
        user = get_user_model().objects.create_user(
            user_id=user_id,
            password=password,
        )
        self.assertEqual(user.user_id, user_id)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_staff)

    def test_new_user_invalid_user_id(self) -> None:
        """
        Tests creating a new user with no user_id raises an error.
        """
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(user_id="", password="test123")

    def test_create_superuser(self) -> None:
        """
        Tests creating a new superuser.
        """
        user = get_user_model().objects.create_superuser(
            user_id="test", password="test123"
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_wave(self) -> None:
        """
        Tests creating a new wave with its information fields.
        """
        wave = models.Wave.objects.create(
            start_date="2021-01-01",
            end_date="2021-01-01",
            created_at="2021-01-01",
            client_id="test",
            wave_number=1,
            wave_name="test",
            wave_type="test",
            wave_status="test",
        )
        self.assertEqual(wave.wave_name, "test")
        self.assertEqual(wave.wave_type, "test")
        self.assertEqual(wave.wave_status, "test")
        self.assertEqual(wave.wave_number, 1)
        self.assertEqual(wave.client_id, "test")
        self.assertEqual(wave.start_date, "2021-01-01")
