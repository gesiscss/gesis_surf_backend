"""
URLs for the mobile events API.
"""

from django.urls import path
from mobile.capture import views

app_name = "capture"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.MobileEventsView.as_view(), name="mobile-events"),
]
