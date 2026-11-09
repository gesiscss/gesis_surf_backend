"""
Test for tab APIs.
"""

from datetime import datetime, timezone
from typing import Any

import django.db
from core.models import Domain, GlobalSession, Tab, Window
from core.tests.helpers import (
    create_domain,
    create_global_session,
    create_tab,
    create_user,
    create_window,
    detail_url,
)
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from tab.serializers import TabDetailSerializer, TabSerializer

TAB_URL = reverse("tab:tab-list")


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


class PrivateTabApiTests(APITestCase):
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
        # Rwelationship with window and global session
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)

        create_tab(user=self.user, window=window)
        create_tab(user=self.user, window=window)
        create_tab(user=self.user, window=window)

        res = self.client.get(TAB_URL)
        tabs = Tab.objects.all().order_by("created_at")
        serializer = TabSerializer(tabs, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_tabs_limited_to_user(self) -> None:
        """
        Test that tabs for the authenticated user are returned
        """
        # Relationship with window and global session & other user
        user2 = create_user(user_id="test2", password="test123")
        global_session = create_global_session(user=user2)
        window = create_window(user=user2, global_session=global_session)
        create_tab(user=user2, window=window)

        # User 1 tab
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)
        tab = create_tab(user=self.user, window=window)

        res = self.client.get(TAB_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["tab_num"], tab.tab_num)
        self.assertEqual(res.data["results"][0]["window"], tab.window.id)
        self.assertEqual(res.data["results"][0]["user"], tab.user.id)

    def test_get_tab_detail(self) -> None:
        """
        Test retrieving a tab detail.
        """
        # Relationship with window and global session
        global_session: GlobalSession = create_global_session(user=self.user)
        window: Window = create_window(user=self.user, global_session=global_session)
        tab = create_tab(user=self.user, window=window)

        # The URL for the detail of the tab
        url: str = detail_url("tab", tab.id)
        res = self.client.get(url)

        serializer = TabDetailSerializer(tab)
        self.assertEqual(res.data, serializer.data)

    def test_create_tab(self) -> None:
        """
        Test creating a tab
        """
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)

        payload = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "tab_num": "Test Tab ID",
            "window_num": "1",
            "tab_session_id": "session_12345",
            "window": str(window.id),
        }

        res = self.client.post(TAB_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        tab = Tab.objects.get(id=res.data["id"])

        for key, value in payload.items():
            if key == "window":
                self.assertEqual(value, str(tab.window.id))
            else:
                self.assertEqual(value, getattr(tab, key))

    def test_partial_update_tab(self) -> None:
        """
        Test updating a tab with patch
        """
        # Relationship with window and global session
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)
        tab = create_tab(user=self.user, window=window)

        payload = {"start_time": datetime.now(timezone.utc)}
        url = detail_url("tab", tab.id)
        self.client.patch(url, payload)

        tab.refresh_from_db()
        self.assertEqual(tab.start_time, payload["start_time"])

    def test_full_update_tab(self) -> None:
        """
        Test updating a tab with put
        """
        # Relationship with window and global session
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)
        tab = create_tab(user=self.user, window=window)

        payload = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "tab_num": "Test Tab ID",
            "window_num": "1",
            "tab_session_id": "session_12345",
            "window": str(window.id),
        }

        url = detail_url("tab", tab.id)
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

        # Relationship with window and global session
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)
        tab = create_tab(user=self.user, window=window)

        payload = {"user": new_user}
        url = detail_url("tab", tab.id)
        self.client.patch(url, payload)

        tab.refresh_from_db()
        self.assertEqual(tab.user, self.user)

    def test_delete_tab(self) -> None:
        """
        Test deleting a tab
        """
        # Relationship with window and global session
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)
        tab = create_tab(user=self.user, window=window)

        url = detail_url("tab", tab.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Tab.objects.filter(id=tab.id).count(), 0)

    def test_delete_other_user_recipe_error(self) -> None:
        """
        Test that the user cannot delete other user's tab
        """
        user2 = create_user(user_id="test2", password="test123")
        global_session = create_global_session(user=user2)
        window = create_window(user=user2, global_session=global_session)
        tab = create_tab(user=user2, window=window)

        url = detail_url("tab", tab.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Tab.objects.filter(id=tab.id).count(), 1)

    def test_create_tab_with_new_domains(self):
        """
        Test creating a Tab with new domains
        """
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)

        payload: dict[str, Any] = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "tab_num": "Test Tab ID",
            "window_num": "1",
            "tab_session_id": "session_12345",
            "window": str(window.id),
            "domains": [
                {
                    "domain_title": "Test Domain",
                    "domain_url": "Test URL",
                    "domain_fav_icon": "Test Icon",
                    "domain_last_accessed": "Test Status",
                    "start_time": datetime.strptime(
                        "2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=timezone.utc),
                    "closing_time": datetime.strptime(
                        "2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=timezone.utc),
                },
                {
                    "domain_title": "Test Domain 2",
                    "domain_url": "Test URL 2",
                    "domain_fav_icon": "Test Icon 2",
                    "domain_last_accessed": "Test Status 2",
                    "start_time": datetime.strptime(
                        "2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=timezone.utc),
                    "closing_time": datetime.strptime(
                        "2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=timezone.utc),
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
        """Test creating a new tab and attaching existing domains to it"""

        # Relationship with window and global session
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)

        # Create an existing domain first
        domain = Domain.objects.create(
            user=self.user,
            domain_title="Test Domain",
            domain_url="https://test.com",
            domain_fav_icon="test-icon.png",
            domain_last_accessed="2024-06-01T17:00:00Z",
            start_time=datetime.now(timezone.utc),
            closing_time=datetime.now(timezone.utc),
            domain_session_id="domain_12345",
            category_number="1",
            criteria_classification="full_allow",
            category_label="test",
            snapshot_html="<html></html>",
        )

        # Create a new tab and attach the existing domain
        payload = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "tab_num": "Test Tab ID",
            "window_num": "1",
            "tab_session_id": "session_12345",
            "window": str(window.id),
            "domain_ids": [str(domain.id)],
        }

        res = self.client.post(TAB_URL, payload, format="json")

        # Verify the results
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Check tab was created
        tab = Tab.objects.get(id=res.data["id"])
        self.assertEqual(tab.user, self.user)

        # Verify domain was attached
        self.assertEqual(tab.domains.count(), 1)
        self.assertEqual(tab.domains.first(), domain)

        # Verify no new domain was created
        self.assertEqual(
            Domain.objects.filter(domain_title=domain.domain_title).count(), 1
        )

    def test_create_domain_with_existing_tab_same_title(self) -> None:
        """
        Create the domain with the same title and check if it is created
        """

        # Relationship with window and global session
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)

        domain_google: "Domain" = Domain.objects.create(
            user=self.user,
            domain_title="Google",
            domain_url="Test URL",
            domain_fav_icon="Test Icon",
            domain_last_accessed="2024-06-01T17:00:00Z",
            domain_session_id="domain_12345",
            start_time=datetime.strptime(
                "2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc),
            closing_time=datetime.strptime(
                "2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc),
            snapshot_html="<html></html>",
        )

        payload: dict[str, Any] = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "snapshot_html": "Test HTML",
            "tab_num": "Test Tab ID",
            "window_num": "1",
            "tab_session_id": "session_12345",
            "window": str(window.id),
            "domain_ids": [str(domain_google.id)],
        }
        res = self.client.post(TAB_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_tab_with_existing_domains(self) -> None:
        """Test creating a Tab with existing domains"""

        # Relationship with window and global session
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)

        # Create an existing domain first
        domain: Domain = create_domain(user=self.user)

        tab = create_tab(user=self.user, window=window)
        tab.domains.add(domain)

        payload: dict[str, Any] = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "snapshot_html": "Test HTML",
            "tab_num": "Test Tab ID",
            "window_num": "1",
            "tab_session_id": "session_12345",
            "window": str(window.id),
            "domain_ids": [str(domain.id)],
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
        Test create a tab with two identical domains.
        """

        # Relationship with window and global session
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)

        # Tab creation
        tab = create_tab(user=self.user, window=window)

        # Domain creation Many to Many relationship
        domain = create_domain(user=self.user)
        tab.domains.add(domain)

        payload: dict[str, Any] = {
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "snapshot_html": "Test HTML",
            "tab_num": "Test Tab ID",
            "window_num": "1",
            "tab_session_id": "session_12345",
            "window": str(window.id),
            "domain_ids": [str(domain.id), str(domain.id)],
        }

        res = self.client.post(TAB_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        tab = Tab.objects.get(id=res.data["id"])
        self.assertEqual(tab.domains.count(), 1)
        self.assertEqual(Domain.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Tab.objects.filter(user=self.user).count(), 2)

    def test_create_tab_with_duplicate_domains(self):
        """
        Test that creating a tab with duplicate domains enforces uniqueness constraints
        """
        # Setup
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)

        # Create payload with two identical domains
        domain_time = datetime.strptime("2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S")
        domain_time = domain_time.replace(tzinfo=timezone.utc)  # Add timezone

        payload = {
            "start_time": datetime.now(timezone.utc).isoformat(),
            "closing_time": datetime.now(timezone.utc).isoformat(),
            "tab_num": "Test Tab ID",
            "window_num": "1",
            "tab_session_id": "session_12345",
            "window": str(window.id),
            "domains": [
                # First domain
                {
                    "domain_title": "Duplicate Domain",
                    "domain_url": "https://duplicate.com",
                    "domain_fav_icon": "favicon.ico",
                    "domain_last_accessed": "2024-06-01T17:00:00Z",
                    "start_time": domain_time.isoformat(),  # Same timestamp
                    "closing_time": domain_time.isoformat(),
                    "domain_session_id": "domain_12345",
                    "category_number": "1",
                    "criteria_classification": "full_allow",
                    "category_label": "test",
                    "snapshot_html": "<html></html>",
                },
                # Second domain with same constraints
                {
                    "domain_title": "Duplicate Domain",
                    "domain_url": "https://duplicate.com",
                    "domain_fav_icon": "favicon2.ico",  # Different icon doesn't matter
                    "domain_last_accessed": "2024-06-01T17:00:00Z",
                    "start_time": domain_time.isoformat(),  # Same timestamp
                    "closing_time": domain_time.isoformat(),
                    "domain_session_id": "domain_12346",  # Different ID doesn't matter
                    "category_number": "2",
                    "criteria_classification": "full_allow",
                    "category_label": "test2",
                    "snapshot_html": "<html></html>",
                },
            ],
        }

        res = self.client.post(TAB_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Exactly one domain persisted; both list entries attached it.
        self.assertEqual(
            Domain.objects.filter(
                domain_title="Duplicate Domain", domain_url="https://duplicate.com"
            ).count(),
            1,
        )
        tab = Tab.objects.get(id=res.data["id"])
        self.assertEqual(tab.domains.count(), 1)

    def test_update_tab_assigned_domain(self) -> None:
        """
        Test updating a tab with assigned domain.

        The legacy domain_updates field is no longer a serializer field:
        DRF ignores unknown payloads, so the request succeeds but the
        domain attributes are NOT updated. This pins the removed
        dead-code path (audit: domain_updates was never a declared
        field, _update_domains was unreachable).
        """

        # Relationship with window and global session
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)
        tab = create_tab(user=self.user, window=window)
        domain = create_domain(user=self.user)
        tab.domains.add(domain)

        payload = {
            "domain_updates": [{"id": str(domain.id), "domain_title": "Test Domain 2"}]
        }

        url = detail_url("tab", tab.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(domain, tab.domains.all())
        domain.refresh_from_db()
        self.assertEqual(domain.domain_title, "example.com")

    def test_create_new_domain_on_update(self) -> None:
        """
        Test creating a new domain on update
        """

        # Relationship with window and global session
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)
        tab = create_tab(user=self.user, window=window)

        url = detail_url("tab", tab.id)
        res = self.client.patch(
            url,
            {
                "domains": [
                    {
                        "domain_title": "Test Domain",
                        "domain_url": "Test URL",
                        "domain_fav_icon": "Test Icon",
                        "domain_last_accessed": "Test Status",
                        "start_time": datetime.strptime(
                            "2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
                        ).replace(tzinfo=timezone.utc),
                        "closing_time": datetime.strptime(
                            "2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
                        ).replace(tzinfo=timezone.utc),
                        "snapshot_html": "<html></html>",
                    }
                ]
            },
            format="json",
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_domain = Domain.objects.get(domain_title="Test Domain")
        self.assertIn(new_domain, tab.domains.all())

    def test_create_domain_on_update_with_existing_domain(self) -> None:
        """
        Test creating a domain on update with existing domain
        """

        # Relationship with window and global session
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)
        tab = create_tab(user=self.user, window=window)

        domain = Domain.objects.create(
            user=self.user,
            domain_title="Test Domain",
            domain_url="Test URL",
            domain_fav_icon="Test Icon",
            domain_last_accessed="Test Status",
            start_time=datetime.strptime(
                "2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc),
            closing_time=datetime.strptime(
                "2024-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc),
            snapshot_html="<html></html>",
            domain_session_id="domain_12345",
        )
        tab.domains.add(domain)

        domain_dos = create_domain(user=self.user)

        url = detail_url("tab", tab.id)
        res = self.client.patch(
            url, {"domain_ids": [str(domain.id), str(domain_dos.id)]}, format="json"
        )

        tab.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(domain, tab.domains.all())
        self.assertEqual(tab.domains.count(), 2)

    def test_patch_with_foreign_domain_id_rejected(self) -> None:
        """
        BOLA regression (audit P0 #1): attaching another user's domain via
        domain_ids must fail with 400 and must not attach the domain.
        """
        user_b = create_user(user_id="attacker_b", password="testpass12345")
        domain_b = create_domain(user=user_b)

        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)
        tab = create_tab(user=self.user, window=window)

        url = detail_url("tab", tab.id)
        res = self.client.patch(
            url, {"domain_ids": [str(domain_b.id)]}, format="json"
        )

        tab.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn(domain_b, tab.domains.all())

    def test_patch_with_own_domain_id_accepted(self) -> None:
        """
        BOLA regression (audit P0 #1): attaching one's own domain via
        domain_ids still works (the extension's normal attach flow).
        """
        domain = create_domain(user=self.user)

        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)
        tab = create_tab(user=self.user, window=window)

        url = detail_url("tab", tab.id)
        res = self.client.patch(
            url, {"domain_ids": [str(domain.id)]}, format="json"
        )

        tab.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(domain, tab.domains.all())

    def test_tab_response_does_not_leak_domain_owner(self) -> None:
        """
        BOLA regression (audit #14): the nested domain objects in tab
        responses must not expose the owner's user UUID.
        """
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)
        tab = create_tab(user=self.user, window=window)
        domain = create_domain(user=self.user)
        tab.domains.add(domain)

        url = detail_url("tab", tab.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        domain_keys = set(res.data["domains"][0].keys())
        self.assertNotIn("user", domain_keys)
        for key in domain_keys:
            self.assertNotIn(
                key, ["user"], "owner field must not be serialized"
            )

    def test_create_tab_with_long_url_domain(self) -> None:
        """
        D9 regression: an 8 KB domain_url saves in full (the extension
        data-loss investigation found the old index could reject long
        URLs; the fingerprint index cannot overflow).
        """
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)

        payload = {
            "start_time": datetime.now(timezone.utc).isoformat(),
            "closing_time": datetime.now(timezone.utc).isoformat(),
            "tab_num": "Test Tab ID",
            "window_num": "1",
            "tab_session_id": "session_12345",
            "window": str(window.id),
            "domains": [
                {
                    "domain_title": "T" * 8000,
                    "domain_url": "https://example.com/" + "u" * 8000,
                    "domain_fav_icon": "Test Icon",
                    "domain_last_accessed": "Test Status",
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "closing_time": datetime.now(timezone.utc).isoformat(),
                    "snapshot_html": "<html></html>",
                }
            ],
        }

        res = self.client.post(TAB_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        tab = Tab.objects.get(id=res.data["id"])
        domain = tab.domains.first()
        self.assertEqual(len(domain.domain_url), len("https://example.com/") + 8000)
        self.assertEqual(len(domain.domain_title), 8000)

    def test_resend_same_domain_is_idempotent(self) -> None:
        """
        D9b regression: resending the exact same domain payload (an
        extension retry after a lost response) succeeds and re-attaches
        the existing row instead of failing on the unique constraint.
        The tab identifiers differ per request (a retry creates a new
        tab row; only the domain payload is resent verbatim).
        """
        global_session = create_global_session(user=self.user)
        window = create_window(user=self.user, global_session=global_session)

        base_payload = {
            "start_time": datetime.now(timezone.utc).isoformat(),
            "closing_time": datetime.now(timezone.utc).isoformat(),
            "tab_num": "Test Tab ID",
            "window_num": "1",
            "tab_session_id": "session_12345",
            "window": str(window.id),
            "domains": [
                {
                    "domain_title": "Retry Domain",
                    "domain_url": "https://retry.com",
                    "domain_fav_icon": "Test Icon",
                    "domain_last_accessed": "Test Status",
                    "start_time": "2024-06-01T17:00:00Z",
                    "closing_time": "2024-06-01T17:00:00Z",
                    "snapshot_html": "<html></html>",
                }
            ],
        }

        first_payload = dict(base_payload, tab_session_id="session_first")
        first = self.client.post(TAB_URL, first_payload, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second_payload = dict(base_payload, tab_session_id="session_second")
        second = self.client.post(TAB_URL, second_payload, format="json")
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)

        # Exactly one domain row; the resend attached the same one.
        self.assertEqual(
            Domain.objects.filter(domain_title="Retry Domain").count(), 1
        )

    def test_two_users_same_domain_url_time_both_save(self) -> None:
        """
        D9 regression: two different users visiting the identical domain
        at the identical microsecond must BOTH save. The user column is
        part of the fingerprint key, so cross-user false collisions are
        impossible.
        """
        user_b = create_user(user_id="user_b_collide", password="testpass12345")
        domain_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        domain_a = Domain.objects.create(
            user=self.user,
            domain_title="Shared Title",
            domain_url="https://shared.example.com",
            domain_fav_icon="Test Icon",
            domain_last_accessed="Test Status",
            start_time=domain_time,
            closing_time=domain_time,
            snapshot_html="<html></html>",
        )
        domain_b = Domain.objects.create(
            user=user_b,
            domain_title="Shared Title",
            domain_url="https://shared.example.com",
            domain_fav_icon="Test Icon",
            domain_last_accessed="Test Status",
            start_time=domain_time,
            closing_time=domain_time,
            snapshot_html="<html></html>",
        )

        self.assertNotEqual(domain_a.id, domain_b.id)
        self.assertEqual(Domain.objects.filter(domain_title="Shared Title").count(), 2)
