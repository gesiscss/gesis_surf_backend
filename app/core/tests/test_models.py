"""
Tests for the models.
"""

from datetime import datetime, timezone
from typing import Any

from core import models
from django.contrib.auth import get_user_model
from django.test import TestCase


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

        wave = models.Wave.objects.create(
            start_date=datetime.strptime("2021-01-01", "%Y-%m-%d"),
            end_date=datetime.strptime("2021-02-28", "%Y-%m-%d"),
            created_at=datetime.now(timezone.utc),
            wave_status="active",
            wave_type="test",
            wave_number="1",
            client_id="test",
        )

        self.assertEqual(wave.start_date, datetime.strptime("2021-01-01", "%Y-%m-%d"))
        self.assertEqual(wave.end_date, datetime.strptime("2021-02-28", "%Y-%m-%d"))
        self.assertEqual(
            self.round_datetime(wave.created_at),
            self.round_datetime(datetime.now(timezone.utc)),
        )
        self.assertEqual(wave.wave_status, "active")
        self.assertEqual(wave.wave_type, "test")
        self.assertEqual(wave.wave_number, "1")
        self.assertEqual(wave.client_id, "test")

    def test_create_window(self) -> None:
        """
        Tests creating a new window.
        """
        user = get_user_model().objects.create_user(user_id="test", password="test123")
        window = models.Window.objects.create(
            user=user,
            start_time=datetime.strptime("2021-06-01 08:00:00", "%Y-%m-%d %H:%M:%S"),
            closing_time=datetime.strptime("2021-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
            created_at=datetime.now(timezone.utc),
            window_num=1,
        )

        self.assertEqual(
            window.start_time,
            datetime.strptime("2021-06-01 08:00:00", "%Y-%m-%d %H:%M:%S"),
        )
        self.assertEqual(
            window.closing_time,
            datetime.strptime("2021-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
        )
        self.assertEqual(
            self.round_datetime(window.created_at),
            self.round_datetime(datetime.now(timezone.utc)),
        )
        self.assertEqual(window.user, user)
        self.assertEqual(window.window_num, 1)

    def test_create_tab(self) -> None:
        """
        Tests creating a new tab instance.
        """
        user = get_user_model().objects.create_user(user_id="test", password="test123")
        tab = models.Tab.objects.create(
            user=user,
            start_time=datetime.strptime("2021-06-01 08:00:00", "%Y-%m-%d %H:%M:%S"),
            closing_time=datetime.strptime("2021-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
            created_at=datetime.now(timezone.utc),
            tab_num="test",
        )
        self.assertEqual(
            tab.start_time,
            datetime.strptime("2021-06-01 08:00:00", "%Y-%m-%d %H:%M:%S"),
        )
        self.assertEqual(
            tab.closing_time,
            datetime.strptime("2021-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
        )
        self.assertEqual(
            self.round_datetime(tab.created_at),
            self.round_datetime(datetime.now(timezone.utc)),
        )
        self.assertEqual(tab.user, user)
        self.assertEqual(tab.tab_num, "test")

    def test_create_domain(self) -> None:
        """
        Tests creating a new domain instance.
        """
        user = get_user_model().objects.create_user(user_id="test", password="test123")
        domain = models.Domain.objects.create(
            user=user,
            domain_title="Test",
            domain_url="https://www.test.com",
            domain_fav_icon="test.ico",
            domain_status="active",
            start_time=datetime.strptime("2021-06-01 08:00:00", "%Y-%m-%d %H:%M:%S"),
            closing_time=datetime.strptime("2021-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
            snapshot_html="test",
            created_at=datetime.now(timezone.utc),
        )
        self.assertEqual(domain.domain_title, "Test")
        self.assertEqual(domain.domain_url, "https://www.test.com")
        self.assertEqual(domain.domain_fav_icon, "test.ico")
        self.assertEqual(domain.domain_status, "active")
        self.assertEqual(
            self.round_datetime(domain.created_at),
            self.round_datetime(datetime.now(timezone.utc)),
        )
        self.assertEqual(domain.user, user)
        self.assertEqual(
            domain.start_time,
            datetime.strptime("2021-06-01 08:00:00", "%Y-%m-%d %H:%M:%S"),
        )
        self.assertEqual(
            domain.closing_time,
            datetime.strptime("2021-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
        )
        self.assertEqual(domain.snapshot_html, "test")

    def test_create_click(self) -> None:
        """
        Test creating a new click instance.
        """
        user = get_user_model().objects.create_user(user_id="test", password="test123")
        click = models.Click.objects.create(
            user=user,
            click_time=datetime.strptime("2021-06-01 08:00:00", "%Y-%m-%d %H:%M:%S"),
            click_type="click",
            click_location="test",
            created_at=datetime.now(timezone.utc),
            domain=models.Domain.objects.create(
                user=user,
                domain_title="Test",
                domain_url="https://www.test.com",
                domain_fav_icon="test.ico",
                domain_status="active",
                created_at=datetime.now(timezone.utc),
            ),
        )
        self.assertEqual(
            click.click_time,
            datetime.strptime("2021-06-01 08:00:00", "%Y-%m-%d %H:%M:%S"),
        )
        self.assertEqual(click.click_type, "click")
        self.assertEqual(click.click_location, "test")
        self.assertEqual(
            self.round_datetime(click.created_at),
            self.round_datetime(datetime.now(timezone.utc)),
        )
        self.assertEqual(click.user, user)

    def test_create_scroll(self):
        """
        Test creating a new scroll instance.
        """
        user = get_user_model().objects.create_user(user_id="test", password="test123")
        scroll = models.Scroll.objects.create(
            user=user,
            scroll_time=datetime.strptime("2021-06-01 08:00:00", "%Y-%m-%d %H:%M:%S"),
            scroll_x=0,
            scroll_y=0,
            page_x_offset=0,
            page_y_offset=0,
            created_at=datetime.now(timezone.utc),
            # Create the domain_id for the scroll
            domain=models.Domain.objects.create(
                user=user,
                domain_title="Test",
                domain_url="https://www.test.com",
                domain_fav_icon="test.ico",
                domain_status="active",
                created_at=datetime.now(timezone.utc),
            ),
        )
        self.assertEqual(
            scroll.scroll_time,
            datetime.strptime("2021-06-01 08:00:00", "%Y-%m-%d %H:%M:%S"),
        )
        self.assertEqual(scroll.scroll_x, 0)
        self.assertEqual(scroll.scroll_y, 0)
        self.assertEqual(scroll.page_x_offset, 0)
        self.assertEqual(scroll.page_y_offset, 0)
        self.assertEqual(
            self.round_datetime(scroll.created_at),
            self.round_datetime(datetime.now(timezone.utc)),
        )
        self.assertEqual(scroll.user, user)

    def test_create_host(self) -> None:
        """
        Test creating a new url instance.
        """
        host = models.Host.objects.create(
            hostname="https://www.test.com",
            created_at=datetime.now(timezone.utc),
        )
        self.assertEqual(host.hostname, "https://www.test.com")
        self.assertEqual(
            self.round_datetime(host.created_at),
            self.round_datetime(datetime.now(timezone.utc)),
        )

    def test_create_category(self) -> None:
        """
        Test creating a new category instance.
        """
        category = models.Category.objects.create(
            category_score=0.0,
            category_parent="test",
            category_label="test",
            category_confidence=0.0,
            created_at=datetime.now(timezone.utc),
            criteria=models.Criteria.objects.create(
                criteria_classification="test",
                criteria_window=True,
                criteria_tab=True,
                criteria_domain=True,
                criteria_click=True,
                criteria_scroll=True,
            ),
        )
        self.assertEqual(category.category_score, 0.0)
        self.assertEqual(category.category_parent, "test")
        self.assertEqual(category.category_label, "test")
        self.assertEqual(category.category_confidence, 0.0)
        self.assertEqual(
            self.round_datetime(category.created_at),
            self.round_datetime(datetime.now(timezone.utc)),
        )

    def test_create_criteria(self) -> None:
        """
        Test creating a new criteria instance.
        """
        criteria = models.Criteria.objects.create(
            criteria_classification="test",
            criteria_window=True,
            criteria_tab=True,
            criteria_domain=True,
            criteria_click=True,
            criteria_scroll=True,
        )
        self.assertEqual(criteria.criteria_classification, "test")
        self.assertEqual(criteria.criteria_window, True)
        self.assertEqual(criteria.criteria_tab, True)
        self.assertEqual(criteria.criteria_domain, True)
        self.assertEqual(criteria.criteria_click, True)
        self.assertEqual(criteria.criteria_scroll, True)
