"""
Request-local domain results in tab API responses.
"""

from core.models import Domain
from core.tests.helpers import (
    create_domain,
    create_global_session,
    create_tab,
    create_user,
    create_window,
    detail_url,
)
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from tab.serializers import DomainSerializer


class CreatedDomainsTests(APITestCase):
    def setUp(self):
        self.user = create_user(user_id="created-domains-owner")
        self.client.force_authenticate(self.user)
        session = create_global_session(user=self.user)
        self.window = create_window(user=self.user, global_session=session)
        self.tab = create_tab(user=self.user, window=self.window)
        self.url = detail_url("tab", self.tab.pk)
        self.domain = {
            "domain_title": "Example",
            "domain_url": "https://example.com/page",
            "domain_last_accessed": "2026-11-09T12:00:00Z",
            "domain_session_id": "scope-windowId-1-tabId-2-domain-example-visit",
            "start_time": "2026-11-09T12:00:00Z",
            "closing_time": "2026-11-09T12:01:00Z",
        }
        self.payload = {
            "start_time": "2026-11-09T12:00:00Z",
            "closing_time": "2026-11-09T12:01:00Z",
            "window": str(self.window.pk),
            "window_num": "1",
            "tab_num": "2",
            "tab_session_id": "scope-windowId-1-tabId-2",
            "domains": [self.domain],
        }

    def test_post_returns_created_domains_in_existing_domain_shape(self):
        response = self.client.post(
            reverse("tab:tab-list"), self.payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        domain = Domain.objects.get()
        self.assertEqual(
            response.data["created_domains"], [DomainSerializer(domain).data]
        )
        self.assertEqual(response.data["domains"], response.data["created_domains"])
        self.assertEqual(
            response.data["created_domains"][0]["domain_session_id"],
            self.domain["domain_session_id"],
        )
        self.assertNotIn("user", response.data["created_domains"][0])

    def test_patch_excludes_historical_domains(self):
        historical = create_domain(user=self.user)
        self.tab.domains.add(historical)
        response = self.client.patch(
            self.url, {"domains": [self.domain]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["domains"]), 2)
        self.assertEqual(len(response.data["created_domains"]), 1)
        self.assertNotEqual(
            str(response.data["created_domains"][0]["id"]), str(historical.pk)
        )

    def test_post_retry_returns_same_domain_uuid(self):
        first = self.client.post(reverse("tab:tab-list"), self.payload, format="json")
        second = self.client.post(
            reverse("tab:tab-list"),
            {**self.payload, "tab_session_id": "scope-retry"},
            format="json",
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(first.data["created_domains"], second.data["created_domains"])
        self.assertEqual(Domain.objects.count(), 1)

    def test_patch_retry_returns_same_domain_uuid(self):
        first = self.client.patch(self.url, {"domains": [self.domain]}, format="json")
        second = self.client.patch(self.url, {"domains": [self.domain]}, format="json")
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data["created_domains"], second.data["created_domains"])
        self.assertEqual(Domain.objects.count(), 1)

    def test_multiple_nested_domains_are_deduplicated_in_input_order(self):
        second = {
            **self.domain,
            "domain_url": "https://example.com/other",
            "domain_session_id": "scope-other-visit",
        }
        response = self.client.patch(
            self.url, {"domains": [self.domain, second, self.domain]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [
                domain["domain_session_id"]
                for domain in response.data["created_domains"]
            ],
            [self.domain["domain_session_id"], second["domain_session_id"]],
        )
        self.assertEqual(Domain.objects.count(), 2)

    def test_reads_have_no_request_created_domains(self):
        self.client.patch(self.url, {"domains": [self.domain]}, format="json")
        detail = self.client.get(self.url)
        listing = self.client.get(reverse("tab:tab-list"))
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["created_domains"], [])
        self.assertTrue(
            all(item["created_domains"] == [] for item in listing.data["results"])
        )

    def test_no_nested_domains_returns_empty_result(self):
        for payload in ({}, {"domains": []}, {"tab_num": "updated"}):
            with self.subTest(payload=payload):
                response = self.client.patch(self.url, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["created_domains"], [])
        payload = {
            key: value for key, value in self.payload.items() if key != "domains"
        }
        response = self.client.post(reverse("tab:tab-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created_domains"], [])

    def test_domain_ids_attachment_is_not_reported_as_creation(self):
        domain = create_domain(user=self.user)
        response = self.client.patch(
            self.url, {"domain_ids": [str(domain.pk)]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created_domains"], [])
        self.assertEqual(len(response.data["domains"]), 1)

    def test_created_domains_input_is_ignored(self):
        response = self.client.patch(
            self.url,
            {"created_domains": [self.domain]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created_domains"], [])
        self.assertFalse(Domain.objects.exists())
