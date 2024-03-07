"""
Test for tab APIs.
"""

from datetime import datetime, timezone
from typing import Any

from core.models import Domain, Tab
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from tab.serializers import TabDetailSerializer, TabSerializer

TAB_URL = reverse("tab:tab-list")


def round_datetime(d_t: datetime) -> datetime:
    """
    Round the datetime to the nearest second.
    """
    return d_t.replace(second=0, microsecond=0)


def create_user(**params):
    """
    Create and return a sample user
    """
    return get_user_model().objects.create_user(**params)


def create_tab(user, **params) -> Tab:
    """
    Create and return a sample tab
    """
    defaults = {
        "start_time": datetime.now(timezone.utc),
        "closing_time": datetime.strptime("2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
        "tab_num": "Test Tab ID",
        "window_num": 1,  # it isnot unique such that can close the tab
    }
    defaults.update(params)
    tab = Tab.objects.create(user=user, **defaults)
    return tab


def detail_url(tab_id) -> str:
    """
    Create and return a tab detail URL
    """
    # The URL for the detail of the tab with the id
    return reverse("tab:tab-detail", args=[tab_id])


class PublicTabApiTests(TestCase):
    """
    Test the publicly available tab API
    """

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self) -> None:
        """
        Test that authentication is required
        """
        res = self.client.get(TAB_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTabApiTests(TestCase):
    """
    Test authenticated Tab API access.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(user_id="test", password="test123")
        self.client.force_authenticate(self.user)

    def test_auth_required(self) -> None:
        """
        Test that authentication is required
        """
        res = self.client.get(TAB_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrive_tabs(self) -> None:
        """
        Test retrieving a list of tabs
        """
        create_tab(user=self.user)
        create_tab(user=self.user)
        create_tab(user=self.user)

        res = self.client.get(TAB_URL)
        tabs = Tab.objects.all().order_by("-id")
        serializer = TabSerializer(tabs, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tabs_limited_to_user(self) -> None:
        """
        Test that tabs for the authenticated user are returned
        """
        user2 = get_user_model().objects.create_user(
            user_id="test2", password="test123"
        )
        create_tab(user=user2)
        tab = create_tab(user=self.user)

        res = self.client.get(TAB_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["tab_num"], tab.tab_num)

    def test_get_tab_detail(self) -> None:
        """
        Test retrieving a tab detail.
        """
        tab = create_tab(user=self.user)
        # The URL for the detail of the tab
        url = detail_url(tab.id)
        res = self.client.get(url)

        serializer = TabDetailSerializer(tab)
        self.assertEqual(res.data, serializer.data)

    def test_create_tab(self) -> None:
        """
        Test creating a tab
        """
        payload = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "tab_num": "Test Tab ID",
            "window_num": "1",
        }
        res = self.client.post(TAB_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        tab = Tab.objects.get(id=res.data["id"])
        for key, value in payload.items():
            self.assertEqual(value, getattr(tab, key))

    def test_partial_update_tab(self) -> None:
        """
        Test updating a tab with patch
        """
        tab = create_tab(user=self.user)
        payload = {"start_time": datetime.now(timezone.utc)}
        url = detail_url(tab.id)
        self.client.patch(url, payload)

        tab.refresh_from_db()
        self.assertEqual(tab.start_time, payload["start_time"])

    def test_full_update_tab(self) -> None:
        """
        Test updating a tab with put
        """
        tab = create_tab(user=self.user)
        payload = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "tab_num": "Test Tab ID",
            "window_num": "1",
        }
        url = detail_url(tab.id)
        self.client.put(url, payload)
        tab.refresh_from_db()
        self.assertEqual(tab.start_time, payload["start_time"])
        self.assertEqual(tab.closing_time, payload["closing_time"])
        self.assertEqual(tab.tab_num, payload["tab_num"])
        self.assertEqual(tab.window_num, payload["window_num"])

    def test_user_returns_error(self) -> None:
        """
        Test that the user cannot be updated from tab detail
        """
        new_user = create_user(user_id="test2", password="test123")
        tab = create_tab(user=self.user)

        payload = {"user": new_user}
        url = detail_url(tab.id)
        self.client.patch(url, payload)

        tab.refresh_from_db()
        self.assertEqual(tab.user, self.user)

    def test_delete_tab(self) -> None:
        """
        Test deleting a tab
        """
        tab = create_tab(user=self.user)
        url = detail_url(tab.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Tab.objects.filter(id=tab.id).count(), 0)

    def test_delete_other_user_recipe_error(self) -> None:
        """
        Test that the user cannot delete other user's tab
        """
        user2 = create_user(user_id="test2", password="test123")
        tab = create_tab(user=user2)

        url = detail_url(tab.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Tab.objects.filter(id=tab.id).count(), 1)

    def test_create_tab_with_new_domains(self):
        """
        Test creating a Tab with new domains
        """
        payload: dict[str, Any] = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "tab_num": "Test Tab ID",
            "window_num": "1",
            "domains": [
                {
                    "domain_title": "Test Domain",
                    "domain_url": "Test URL",
                    "domain_fav_icon": "Test Icon",
                    "domain_status": "Test Status",
                    "start_time": datetime.strptime(
                        "2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
                    ),
                    "closing_time": datetime.strptime(
                        "2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
                    ),
                    "snapshot_html": "<html></html>",
                },
                {
                    "domain_title": "Test Domain 2",
                    "domain_url": "Test URL 2",
                    "domain_fav_icon": "Test Icon 2",
                    "domain_status": "Test Status 2",
                    "start_time": datetime.strptime(
                        "2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
                    ),
                    "closing_time": datetime.strptime(
                        "2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
                    ),
                    "snapshot_html": "<html></html>",
                },
            ],
        }
        res = self.client.post(TAB_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        tabs = Tab.objects.filter(user=self.user)
        # Check that the created domains are two.
        self.assertEqual(tabs.count(), 1)
        tab = tabs[0]
        self.assertEqual(tab.domains.count(), 2)
        for domain in payload["domains"]:
            exists = tab.domains.filter(
                domain_title=domain["domain_title"], user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_tab_with_existing_domain(self):
        """
        Test creating a Tab with existing domains
        """
        domain = Domain.objects.create(
            user=self.user,
            domain_title="Test Domain",
            domain_url="Test URL",
            domain_fav_icon="Test Icon",
            domain_status="Test Status",
            start_time=datetime.strptime("2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
            closing_time=datetime.strptime("2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
            snapshot_html="<html></html>",
        )
        payload: dict[str, Any] = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "snapshot_html": "Test HTML",
            "tab_num": "Test Tab ID",
            "window_num": "1",
            "domains": [
                {
                    "domain_title": domain.domain_title,
                    "domain_url": domain.domain_url,
                    "domain_fav_icon": domain.domain_fav_icon,
                    "domain_status": domain.domain_status,
                    "start_time": domain.start_time,
                    "closing_time": domain.closing_time,
                    "snapshot_html": domain.snapshot_html,
                }
            ],
        }
        res = self.client.post(TAB_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        tabs = Tab.objects.filter(user=self.user)
        self.assertEqual(tabs.count(), 1)
        tab = tabs[0]
        self.assertEqual(tab.domains.count(), 1)
        exists = tab.domains.filter(
            domain_title=domain.domain_title, user=self.user
        ).exists()
        self.assertTrue(exists)

    def test_create_domain_with_existing_tab_same_title(self) -> None:
        """
        Create the domain with the same title and check if it is created
        """
        domain_google: "Domain" = Domain.objects.create(
            user=self.user,
            domain_title="Google",
            domain_url="Test URL",
            domain_fav_icon="Test Icon",
            domain_status="Test Status",
            start_time=datetime.strptime("2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
            closing_time=datetime.strptime("2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
            snapshot_html="<html></html>",
        )
        payload: dict[str, Any] = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "snapshot_html": "Test HTML",
            "tab_num": "Test Tab ID",
            "window_num": "1",
            "domains": [
                {
                    "domain_title": domain_google.domain_title,
                    "domain_url": domain_google.domain_url,
                    "domain_fav_icon": domain_google.domain_fav_icon,
                    "domain_status": domain_google.domain_status,
                    "start_time": domain_google.start_time,
                    "closing_time": domain_google.closing_time,
                    "snapshot_html": domain_google.snapshot_html,
                }
            ],
        }
        res = self.client.post(TAB_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_tab_with_existing_domains(self) -> None:
        """Test creating a Tab with existing domains"""
        domain = Domain.objects.create(
            user=self.user,
            domain_title="Test Domain",
            domain_url="Test URL",
            domain_fav_icon="Test Icon",
            domain_status="Test Status",
            start_time=datetime.strptime("2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
            closing_time=datetime.strptime("2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
            snapshot_html="<html></html>",
        )
        tab = create_tab(user=self.user)
        tab.domains.add(domain)
        payload: dict[str, Any] = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "snapshot_html": "Test HTML",
            "tab_num": "Test Tab ID",
            "window_num": "1",
            "domains": [
                {
                    "domain_title": domain.domain_title,
                    "domain_url": domain.domain_url,
                    "domain_fav_icon": domain.domain_fav_icon,
                    "domain_status": domain.domain_status,
                    "start_time": domain.start_time,
                    "closing_time": domain.closing_time,
                    "snapshot_html": domain.snapshot_html,
                }
            ],
        }
        res = self.client.post(TAB_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        tabs = Tab.objects.filter(user=self.user)
        self.assertEqual(tabs.count(), 2)
        tab = tabs[0]
        self.assertEqual(tab.domains.count(), 1)
        exists = tab.domains.filter(
            domain_title=domain.domain_title, user=self.user
        ).exists()
        self.assertTrue(exists)
        tab = tabs[1]
        self.assertEqual(tab.domains.count(), 1)
        exists = tab.domains.filter(
            domain_title=domain.domain_title, user=self.user
        ).exists()
        self.assertTrue(exists)

    def test_create_tab_with_two_identical_domains(self) -> None:
        """
        Test create a tab with two identical domains
        """
        tab = create_tab(user=self.user)
        domain = Domain.objects.create(
            user=self.user,
            domain_title="Test Domain",
            domain_url="Test URL",
            domain_fav_icon="Test Icon",
            domain_status="Test Status",
            start_time=datetime.strptime("2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
            closing_time=datetime.strptime("2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
            snapshot_html="<html></html>",
        )
        tab.domains.add(domain)
        payload: dict[str, Any] = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "snapshot_html": "Test HTML",
            "tab_num": "Test Tab ID",
            "window_num": "1",
            "domains": [
                {
                    "domain_title": domain.domain_title,
                    "domain_url": domain.domain_url,
                    "domain_fav_icon": domain.domain_fav_icon,
                    "domain_status": domain.domain_status,
                    "start_time": domain.start_time,
                    "closing_time": domain.closing_time,
                    "snapshot_html": domain.snapshot_html,
                },
                {
                    "domain_title": domain.domain_title,
                    "domain_url": domain.domain_url,
                    "domain_fav_icon": domain.domain_fav_icon,
                    "domain_status": domain.domain_status,
                    "start_time": domain.start_time,
                    "closing_time": domain.closing_time,
                    "snapshot_html": domain.snapshot_html,
                },
            ],
        }
        res = self.client.post(TAB_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tab.objects.filter(user=self.user).count(), 2)

    def test_create_domain_on_update(self) -> None:
        """
        Test creating a domain on update
        """
        tab = create_tab(user=self.user)

        payload = {"domains": [{"domain_title": "Test Domain"}]}
        url = detail_url(tab.id)
        res = self.client.patch(url, payload, format="json")

        # There is no refresh db since it is a many to many field
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_domain = Domain.objects.get(domain_title="Test Domain")
        self.assertIn(new_domain, tab.domains.all())

    def test_update_tab_assigned_domain(self) -> None:
        """
        Test updating a tab with assigned domain
        """
        domain = Domain.objects.create(
            user=self.user,
            domain_title="Test Domain",
            domain_url="Test URL",
            domain_fav_icon="Test Icon",
            domain_status="Test Status",
            start_time=datetime.strptime("2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
            closing_time=datetime.strptime("2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
            snapshot_html="<html></html>",
        )
        tab = create_tab(user=self.user)
        tab.domains.add(domain)

        payload = {"domains": [{"domain_title": "Test Domain 2"}]}
        url = detail_url(tab.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(domain, tab.domains.all())

    def test_clear_tab_domains(self) -> None:
        """
        Test clearing tab domains
        """
        domain = Domain.objects.create(
            user=self.user,
            domain_title="Test Domain",
            domain_url="Test URL",
            domain_fav_icon="Test Icon",
            domain_status="Test Status",
            start_time=datetime.strptime("2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
            closing_time=datetime.strptime("2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
            snapshot_html="<html></html>",
        )
        tab = create_tab(user=self.user)
        tab.domains.add(domain)
        payload = {"domains": []}
        url = detail_url(tab.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(tab.domains.count(), 0)
