"""
URLs for the TikTok wavelets API.
"""

from django.urls import path
from wavelets.tiktok import views

app_name = "tiktok"

urlpatterns = [
    path("", views.TikTokDataView.as_view(), name="tiktok-data"),
]
