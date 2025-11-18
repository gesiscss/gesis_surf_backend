"""
Test the maintenance mode mixin
"""

from datetime import datetime, timezone

from core.tests.helpers import create_user
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

DOMAIN_URL = reverse("domain:domain-list")
CREATE_USER_URL = reverse("user:create")
TAB_URL = reverse("tab:tab-list")


class PrivateDomainApiTestsMaintenance(APITestCase):
    """
    Test the domain API (private)
    """

    def setUp(self) -> None:  # pylint: disable=invalid-name
        """
        Set up the test
        """
        self.client = APIClient()
        self.super_user = create_user(
            user_id="testuser",
            password="testpass",
        )
        self.client.force_authenticate(user=self.super_user)
        settings.MAINTENANCE_MODE = False

    def tearDown(self) -> None:  # pylint: disable=invalid-name
        """
        Clean up the test
        """
        settings.MAINTENANCE_MODE = False

    @override_settings(MAINTENANCE_MODE=True)
    def test_maintenance_mode_does_not_block_user(self) -> None:
        """Test that maintenance mode blocks all CRUD operations but user operations"""

        user_id = "testuser_dos"
        payload = {
            "user_id": user_id,
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

        # Test CREATE user
        create_response = self.client.post(CREATE_USER_URL, payload, format="json")
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)

        # Test GET user
        get_response = self.client.get(reverse("user:me"))
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

        # Test UPDATE user
        update_response = self.client.patch(reverse("user:me"), {"password": "newpass"})
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

    @override_settings(MAINTENANCE_MODE=True)
    def test_create_basic_domain_under_maintenance(self) -> None:
        """
        Test creating domain under maintenance mode
        """

        payload = {
            "domain_title": "test.com",
            "domain_url": "https://test.com",
            "domain_fav_icon": "https://test.com/favicon.ico",
            "domain_last_accessed": "active",
            "domain_session_id": "session123",
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "snapshot_html": "<html>Test</html>",
        }
        res = self.client.post(DOMAIN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(
            res.data["detail"],
            "Service temporarily unavailable, please try again later.",
        )

    @override_settings(MAINTENANCE_MODE=True)
    def test_update_domain_under_maintenance(self) -> None:
        """
        Test updating domain under maintenance mode
        """

        payload = {
            "domain_title": "test.com",
            "domain_url": "https://test.com",
            "domain_fav_icon": "https://test.com/favicon.ico",
            "domain_session_id": "session123",
            "domain_last_accessed": "active",
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "snapshot_html": "<html>Test</html>",
        }
        res = self.client.patch(DOMAIN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(
            res.data["detail"],
            "Service temporarily unavailable, please try again later.",
        )
