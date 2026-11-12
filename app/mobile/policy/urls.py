"""
URLs for the mobile policy API.
"""

from django.urls import path
from mobile.policy import views

app_name = "policy"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.MobilePolicyView.as_view(), name="mobile-policy"),
]
