"""
Helper functions for tests.
"""

import random
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from core.models import Click, Domain, GlobalSession, Scroll, Tab, Window
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.urls import reverse


def round_datetime(d_t: datetime | None) -> datetime | None:
    """
    Round the datetime to the nearest second.
    """
    if d_t is None:
        return None
    return d_t.replace(second=0, microsecond=0)


def detail_url(path: str, resource_id: UUID) -> str:
    """
    Create and return a detail URL for a given resource
    """
    return reverse(f"{path}:{path}-detail", args=[resource_id])


# Create a sample user
def create_user(**params: Any) -> AbstractUser:
    """
    Create and return a sample user
    """
    return get_user_model().objects.create_user(**params)


# Create a sample global session
def create_global_session(user: AbstractUser, **params: Any) -> GlobalSession:
    """
    Create and return a sample global session
    """
    defaults: dict[str, Any] = {
        "start_time": datetime.now(timezone.utc),
        "global_session_id": f"session_{random.randint(10000, 99999)}",
    }
    defaults.update(params)

    return GlobalSession.objects.create(user=user, **defaults)


def create_window(user, **params):
    """
    Create and return a sample window
    """
    defaults = {
        "start_time": datetime.now(timezone.utc),
        "closing_time": datetime(2024, 6, 1, 17, 0, 0, tzinfo=timezone.utc),
        "window_num": random.randint(1, 100),
        # Window session ID unique
        "window_session_id": f"session_{random.randint(10000, 99999)}",
        # Global session ID relation
        "global_session": None,
    }
    # Update the defaults with the params provided in the function.
    defaults.update(params)
    return Window.objects.create(user=user, **defaults)


def create_tab(user, **params) -> Tab:
    """
    Create and return a sample tab
    """
    defaults = {
        "start_time": datetime.now(timezone.utc),
        "closing_time": datetime(2024, 6, 1, 17, 0, 0, tzinfo=timezone.utc),
        "tab_num": "Test Tab ID",
        "window_num": 1,  # it is not unique such that can close the tab
        "tab_session_id": f"session_{user.id}_{datetime.now().timestamp()}",
        "window": None,
    }
    defaults.update(params)
    tab = Tab.objects.create(user=user, **defaults)
    return tab


def create_domain(user, **params) -> Domain:
    """
    Create and return a sample domain
    """
    defaults = {
        "domain_title": "example.com",
        "domain_url": "https://www.example.com",
        "domain_fav_icon": "https://www.example.com/favicon.ico",
        "domain_last_accessed": datetime.now(timezone.utc),
        "domain_session_id": f"session_{user.id}_{datetime.now().timestamp()}",
        "start_time": datetime.now(timezone.utc),
        "closing_time": datetime(2024, 6, 1, 17, 0, 0, tzinfo=timezone.utc),
        "snapshot_html": "<html></html>",
    }
    defaults.update(params)
    domain = Domain.objects.create(user=user, **defaults)
    return domain


def create_click(user, **params) -> Click:
    """
    Create and return a sample click
    """

    defaults = {
        "click_type": "click",
        "click_time": datetime(2024, 6, 1, 17, 0, 0, tzinfo=timezone.utc),
        "click_target_element": "button",
        "click_target_tag": "button",
        "click_target_class": "btn",
        "click_target_id": "btn-1",
        "click_page_x": 100,
        "click_page_y": 200,
        "click_referrer": "https://test.com",
        "domain": create_domain(user=user),
    }
    defaults.update(params)
    return Click.objects.create(user=user, **defaults)


def create_scroll(user, **params) -> Scroll:
    """
    Create and return a sample scroll
    """

    defaults = {
        "scroll_x": 0,
        "scroll_y": 0,
        "page_x_offset": 0,
        "page_y_offset": 0,
        "scroll_time": datetime(2024, 6, 1, 17, 0, 0, tzinfo=timezone.utc),
        "domain": create_domain(user=user),
    }
    defaults.update(params)
    return Scroll.objects.create(user=user, **defaults)
