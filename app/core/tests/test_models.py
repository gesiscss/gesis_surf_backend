"""
Tests for the models.
"""

from datetime import datetime
from datetime import timezone
from typing import Any

from django.contrib.auth import get_user_model
from django.test import TestCase

from core import models


def create_user(user_id="test", password="test123") -> Any:
    """
    Helper function to create a user.
    """
    return get_user_model().objects.create_user(user_id=user_id, password=password)


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

    @staticmethod
    def round_datetime(d_t: datetime) -> datetime:
        """
        Rounds a datetime to the nearest minute.
        """
        return d_t.replace(second=0, microsecond=0)

    def test_create_wave(self) -> None:
        """
        Tests creating a new wave.
        """
        user = create_user()
        wave = models.Wave.objects.create(
            user=user,
            start_date=datetime.strptime("2021-01-01", "%Y-%m-%d"),
            end_date=datetime.strptime("2021-02-28", "%Y-%m-%d"),
        )

        self.assertEqual(wave.start_date, datetime.strptime("2021-01-01", "%Y-%m-%d"))
        self.assertEqual(wave.end_date, datetime.strptime("2021-02-28", "%Y-%m-%d"))
        self.assertEqual(
            self.round_datetime(wave.created_at),
            self.round_datetime(datetime.now(timezone.utc)),
        )
