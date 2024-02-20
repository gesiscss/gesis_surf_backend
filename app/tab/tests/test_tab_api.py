"""
Test for tab APIs.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tab
from tab.serializers import TabDetailSerializer
from tab.serializers import TabSerializer

TAB_URL = reverse("tab:tab-list")


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
        "start_time": "2024-06-01 16:00:00",
        "closing_time": "2024-06-01 17:00:00",
        "snapshot_html": "Test HTML",
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
        self.assertEqual(res.data[0]["tab_id"], tab.tab_id)

    def test_get_tab_detail(self) -> None:
        """
        Test retrieving a tab detail.
        """
        tab = create_tab(user=self.user)
        # The URL for the detail of the tab
        url = detail_url(tab.tab_id)
        res = self.client.get(url)

        serializer = TabSerializer(tab)
        self.assertEqual(res.data, serializer.data)
