"""
Tests for the Django admin modifications.
"""
from django.contrib.auth import get_user_model
from django.test import Client
from django.test import TestCase
from django.urls import reverse


class AdminSiteTests(TestCase):
    """
    Tests for the Django admin modifications.
    """

    def setUp(self) -> None:
        """Creates a client and a user for the tests."""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            user_id="admin",
            token_gesis="admin123",
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            user_id="test",
            token_gesis="test123",
        )

    def test_users_listed(self) -> None:
        """Tests that users are listed on the user page."""
        url = reverse("admin:core_participant_changelist")
        response = self.client.get(url)

        self.assertContains(response, self.user.user_id)
