"""
Tests for the models.
"""

from datetime import datetime, timezone

from core import models
from core.tests.helpers import (
    create_click,
    create_domain,
    create_global_session,
    create_scroll,
    create_tab,
    create_user,
    create_window,
    round_datetime,
)
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class ModelTests(APITestCase):
    """
    Tests for the models.
    """

    def test_create_user_with_password(self) -> None:
        """
        Tests creating a new user with a providen token.
        """
        user = create_user(user_id="test", password="test123")
        self.assertIsInstance(user, models.User)
        self.assertEqual(user.user_id, "test")  # type: ignore - user_id is a custom field
        self.assertTrue(user.check_password("test123"))
        self.assertFalse(user.is_staff)

    def test_new_user_invalid_user_id(self) -> None:
        """
        Tests creating a new user with no user_id raises an error.
        """
        with self.assertRaises(ValueError):
            create_user(user_id="", password="test123")

    def test_create_superuser(self) -> None:
        """
        Tests creating a new superuser.
        """
        user = get_user_model().objects.create_superuser(
            user_id="test", password="test123"
        )  # type: ignore -We have overridden the create_superuser method
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

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
            round_datetime(wave.created_at),
            round_datetime(datetime.now(timezone.utc)),
        )
        self.assertEqual(wave.wave_status, "active")
        self.assertEqual(wave.wave_type, "test")
        self.assertEqual(wave.wave_number, "1")
        self.assertEqual(wave.client_id, "test")

    def test_create_window(self) -> None:
        """
        Tests creating a new window.
        """
        user = get_user_model().objects.create_user(
            user_id="test", password="test123"
        )  # type: ignore -We have overridden the create_user method

        # Relationship with global session
        global_session = create_global_session(user=user)
        window = create_window(user=user, global_session=global_session)

        self.assertEqual(window.start_time, window.start_time)
        self.assertEqual(window.closing_time, window.closing_time)
        self.assertEqual(window.user, user)

    def test_create_tab(self) -> None:
        """
        Tests creating a new tab instance.
        """
        user = create_user(user_id="test", password="test123")
        global_session = create_global_session(user=user)
        window = create_window(user=user, global_session=global_session)
        tab = create_tab(user=user, window=window, tab_num="test")
        self.assertEqual(tab.start_time, tab.start_time)
        self.assertEqual(tab.closing_time, tab.closing_time)
        self.assertEqual(tab.window, window)
        self.assertEqual(tab.user, user)
        self.assertEqual(tab.tab_num, "test")

    def test_create_domain(self) -> None:
        """
        Tests creating a new domain instance.
        """
        user = get_user_model().objects.create_user(
            user_id="test", password="test123"
        )  # type: ignore -We have overridden the create_user method
        domain = create_domain(user=user, domain_url="https://www.test.com")
        self.assertEqual(domain.user, user)
        self.assertEqual(domain.domain_title, "example.com")
        self.assertEqual(domain.domain_url, "https://www.test.com")

    def test_create_click(self) -> None:
        """
        Test creating a new click instance.
        """
        user = get_user_model().objects.create_user(
            user_id="test", password="test123"
        )  # type: ignore -We have overridden the create_user method
        click = create_click(user=user)
        self.assertEqual(click.user, user)
        self.assertEqual(click.click_type, "click")
        self.assertEqual(click.click_target_element, "button")

    def test_create_scroll(self):
        """
        Test creating a new scroll instance.
        """
        user = get_user_model().objects.create_user(
            user_id="test", password="test123"
        )  # type: ignore -We have overridden the create_user method
        scroll = create_scroll(user=user)
        self.assertEqual(scroll.user, user)
        self.assertEqual(scroll.scroll_x, 0)
        self.assertEqual(scroll.scroll_y, 0)

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
            round_datetime(host.created_at),
            round_datetime(datetime.now(timezone.utc)),
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
            round_datetime(category.created_at),
            round_datetime(datetime.now(timezone.utc)),
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

    def test_create_category_with_instance_criteria(self) -> None:
        """
        Test creating a new category instance with an instance of criteria.
        """
        criteria = models.Criteria.objects.create(
            criteria_classification="test",
            criteria_window=True,
            criteria_tab=True,
            criteria_domain=True,
            criteria_click=True,
            criteria_scroll=True,
        )
        category = models.Category.objects.create(
            category_score=0.0,
            category_parent="test",
            category_label="test",
            category_confidence=0.0,
            created_at=datetime.now(timezone.utc),
            criteria=criteria,
        )
        self.assertEqual(category.category_score, 0.0)
        self.assertEqual(category.category_parent, "test")
        self.assertEqual(category.category_label, "test")
        self.assertEqual(category.category_confidence, 0.0)
        self.assertEqual(
            round_datetime(category.created_at),
            round_datetime(datetime.now(timezone.utc)),
        )

    def test_create_host_with_category_and_criteria(self) -> None:
        """
        Test creating a new host instance with an instance of category and criteria.
        """
        criteria = models.Criteria.objects.create(
            criteria_classification="test",
            criteria_window=True,
            criteria_tab=True,
            criteria_domain=True,
            criteria_click=True,
            criteria_scroll=True,
        )
        category = models.Category.objects.create(
            category_score=0.0,
            category_parent="test",
            category_label="test",
            category_confidence=0.0,
            created_at=datetime.now(timezone.utc),
            criteria=criteria,
        )
        host = models.Host.objects.create(
            hostname="https://www.test.com",
            created_at=datetime.now(timezone.utc),
        )
        host.categories.add(category)
        self.assertEqual(host.hostname, "https://www.test.com")
        self.assertEqual(
            round_datetime(host.created_at),
            round_datetime(datetime.now(timezone.utc)),
        )

    def test_create_category_without_criteria(self) -> None:
        """
        Test creating a new category instance without an instance of criteria.
        """
        category = models.Category.objects.create(
            category_score=0.0,
            category_parent="test",
            category_label="test",
            category_confidence=0.0,
            created_at=datetime.now(timezone.utc),
        )
        self.assertEqual(category.category_score, 0.0)
        self.assertEqual(category.category_parent, "test")
        self.assertEqual(category.category_label, "test")
        self.assertEqual(category.category_confidence, 0.0)
        self.assertEqual(
            round_datetime(category.created_at),
            round_datetime(datetime.now(timezone.utc)),
        )

    def test_create_privacy(self) -> None:
        """
        Test creating a new privacy instance.
        """
        user = get_user_model().objects.create_user(
            user_id="test", password="test123"
        )  # type: ignore -We have overridden the create_user method
        privacy = models.Privacy.objects.create(
            user=user,
            privacy_mode=False,
            privacy_start_time=datetime.strptime(
                "2021-06-01 08:00:00", "%Y-%m-%d %H:%M:%S"
            ),
            privacy_end_time=datetime.strptime(
                "2021-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"
            ),
        )

        self.assertEqual(privacy.privacy_mode, False)
        self.assertEqual(
            privacy.privacy_start_time,
            datetime.strptime("2021-06-01 08:00:00", "%Y-%m-%d %H:%M:%S"),
        )
        self.assertEqual(
            privacy.privacy_end_time,
            datetime.strptime("2021-06-01 17:00:00", "%Y-%m-%d %H:%M:%S"),
        )
        self.assertEqual(privacy.user, user)

    def test_create_extension(self) -> None:
        """
        Test creating a new extension instance.
        """
        user = get_user_model().objects.create_user(
            user_id="test", password="test123"
        )  # type: ignore -We have overridden the create_user method
        extension = models.Extension.objects.create(
            user=user,
            extension_version="1.0.0",
            extension_installed_at=datetime.now(timezone.utc),
            extension_updated_at=datetime.now(timezone.utc),
            extension_browser="chrome",
        )

        self.assertEqual(extension.extension_version, "1.0.0")
        self.assertEqual(
            round_datetime(extension.extension_installed_at),
            round_datetime(datetime.now(timezone.utc)),
        )
        self.assertEqual(extension.extension_browser, "chrome")

    def test_create_global_session(self) -> None:
        """
        Test creating a new global session instance.
        """
        user = get_user_model().objects.create_user(
            user_id="test", password="test123"
        )  # type: ignore -We have overridden the create_user method
        global_session = create_global_session(user=user)
        self.assertEqual(
            global_session.global_session_id, global_session.global_session_id
        )
