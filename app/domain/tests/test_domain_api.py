"""
Test for Domain APIs.
"""

from datetime import datetime, timezone

from core.models import Click, Domain, Scroll
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from domain.serializers import DomainSingleSerializer
from rest_framework import status
from rest_framework.test import APIClient

DOMAIN_URL = reverse("domain:domain-list")
SCROLL_URL: str = reverse("domain:scroll-list")


def detail_url_scroll(scroll: Scroll) -> str:
    """
    Return the scroll detail URL
    """
    return reverse("domain:scroll-detail", args=[scroll.id])


def detail_url(domain_id: int) -> str:
    """
    Return domain detail URL
    """
    return reverse("domain:domain-detail", args=[domain_id])


def create_user(user_id: str = "test", password: str = "testpass"):
    """
    Create and return a sample user
    """
    return get_user_model().objects.create_user(user_id, password)


def create_domain(user, **params) -> Domain:
    """
    Create and return a sample domain
    """
    defaults = {
        "domain_title": "test.com",
        "domain_url": "https://test.com",
        "domain_fav_icon": "https://test.com/favicon.ico",
        "domain_status": "active",
        "start_time": datetime.strptime("2021-06-01 08:00:00", "%Y-%m-%d %H:%M:%S"),
        "closing_time": datetime.strptime("2021-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
        "snapshot_html": "<html>Test</html>",
    }
    defaults.update(params)
    return Domain.objects.create(user=user, **defaults)


def create_scroll(user, domain=None, **params) -> Scroll:
    """
    Create and return a sample scroll
    """
    if domain is None:
        domain = create_domain(user=user)
    defaults = {
        "scroll_x": 0,
        "scroll_y": 0,
        "page_x_offset": 0,
        "page_y_offset": 0,
        "scroll_time": "2024-06-01 17:00:00",
        "domain": domain,
    }
    defaults.update(params)
    return Scroll.objects.create(user=user, **defaults)


def create_click(user, domain=None, **params) -> Click:
    """
    Create and return a sample click
    """
    if domain is None:
        domain = create_domain(user=user)
    defaults = {
        "click_type": "click",
        "click_time": "2024-06-01 17:00:00",
        "click_target_element": "button",
        "click_target_tag": "button",
        "click_target_class": "btn",
        "click_target_id": "btn-1",
        "click_page_x": 100,
        "click_page_y": 200,
        "click_referrer": "https://test.com",
        "domain": domain,
    }
    defaults.update(params)
    return Click.objects.create(user=user, **defaults)


class PublicDomainApiTests(TestCase):
    """
    Test the publicly available domian API
    """

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self) -> None:
        """
        Test that login is required for retrieving domains
        """
        res = self.client.get(DOMAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateDomainApiTests(TestCase):
    """
    Test authenticated Domain API access
    """

    def setUp(self) -> None:
        """
        Setup the authenticated user
        """
        self.client = APIClient()
        self.user = create_user(user_id="test", password="test123")
        self.client.force_authenticate(self.user)

    def test_retrieve_domains(self) -> None:
        """
        Test retrieving domains
        """
        create_domain(user=self.user)
        create_domain(user=self.user)
        create_domain(user=self.user)

        res = self.client.get(DOMAIN_URL)
        domains = Domain.objects.all().order_by("-created_at")
        serializer = DomainSingleSerializer(domains, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_domains_limited_to_user(self) -> None:
        """
        Test that domains for the authenticated user are returned
        """
        user2 = get_user_model().objects.create_user(
            user_id="other", password="testpass"
        )
        create_domain(user=user2)
        domain = create_domain(user=self.user)

        res = self.client.get(DOMAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["domain_title"], domain.domain_title)

    def test_get_domain_detail(self) -> None:
        """
        Test retrieving a domain detail
        """
        domain = create_domain(user=self.user)
        url = detail_url(domain.id)
        res = self.client.get(url)
        serializer = DomainSingleSerializer(domain)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_domain(self) -> None:
        """
        Test creating domain
        """
        payload = {
            "domain_title": "test.com",
            "domain_url": "https://test.com",
            "domain_fav_icon": "https://test.com/favicon.ico",
            "domain_status": "active",
            "start_time": datetime.now(timezone.utc),
            "closing_time": datetime.now(timezone.utc),
            "snapshot_html": "<html>Test</html>",
        }
        res = self.client.post(DOMAIN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        domain = Domain.objects.get(id=res.data["id"])
        for key, value in payload.items():
            self.assertEqual(value, getattr(domain, key))

    def test_partial_update_domain(self) -> None:
        """
        Test updating a domain with patch
        """
        domain = create_domain(user=self.user)
        payload = {"domain_title": "test.com", "domain_status": "inactive"}
        url = detail_url(domain.id)
        self.client.patch(url, payload)

        domain.refresh_from_db()
        self.assertEqual(domain.domain_status, payload["domain_status"])

    def test_full_update_domain(self) -> None:
        """
        Test updating a domain with put
        """
        domain = create_domain(user=self.user)
        payload = {
            "domain_title": "test.com",
            "domain_url": "https://test.com",
            "domain_fav_icon": "https://test.com/favicon.ico",
            "domain_status": "inactive",
            "start_time": datetime.strptime("2021-06-01 08:00:00", "%Y-%m-%d %H:%M:%S"),
            "closing_time": datetime.strptime(
                "2021-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
            ),
            "snapshot_html": "<html>Test</html>",
        }
        url = detail_url(domain.id)
        self.client.put(url, payload)
        domain.refresh_from_db()
        self.assertEqual(domain.domain_title, payload["domain_title"])

    def test_user_returns_error(self) -> None:
        """
        Test that the user cannot be updated from domain detail.
        """
        new_user = create_user(user_id="new", password="newpass")
        domain = create_domain(user=self.user)
        payload = {"user": new_user}
        url = detail_url(domain.id)
        self.client.put(url, payload)

        domain.refresh_from_db()
        self.assertNotEqual(domain.user, new_user)

    def test_delete_domain(self) -> None:
        """
        Test deleting a domain
        """
        domain = create_domain(user=self.user)
        url = detail_url(domain.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Domain.objects.count(), 0)

    def test_create_domain_with_new_scroll(self) -> None:
        """
        Test creating a domain with a new scroll
        """
        create_scroll(user=self.user)
        self.assertEqual(Scroll.objects.count(), 1)
        self.assertEqual(Domain.objects.count(), 1)
        domains = Domain.objects.filter(user=self.user)
        scrolls = domains[0].scrolls.all()
        self.assertEqual(domains.count(), 1)
        self.assertEqual(scrolls.count(), 1)
        for scroll in scrolls:
            self.assertEqual(scroll.user, self.user)
            self.assertEqual(scroll.domain, domains[0])
            self.assertEqual(scroll.scroll_x, 0)

    def test_create_domain_with_new_scroll_and_click(self) -> None:
        """
        Test creating a domain with a new scroll and click
        """
        domain = create_domain(user=self.user)
        click = create_click(user=self.user, domain=domain)
        scroll = create_scroll(user=self.user, domain=domain)
        self.assertEqual(Scroll.objects.count(), 1)
        self.assertEqual(Click.objects.count(), 1)
        self.assertEqual(Domain.objects.count(), 1)
        click = domain.clicks.all()
        scroll = domain.scrolls.all()
        self.assertEqual(click.count(), 1)
        self.assertEqual(scroll.count(), 1)

    def test_update_scroll(self) -> None:
        """
        Test updating a scroll
        """
        scroll = create_scroll(user=self.user)
        url = detail_url_scroll(scroll)
        payload = {"scroll_x": 100, "scroll_y": 100, "page_x_offset": 100}
        self.client.patch(url, payload)
        scroll.refresh_from_db()
        self.assertEqual(scroll.scroll_x, payload["scroll_x"])
