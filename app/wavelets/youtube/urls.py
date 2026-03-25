"""
URLs for the YouTube Shorts wavelets API.
"""

from django.urls import path
from wavelets.youtube import views

app_name = "youtube"

urlpatterns = [
    path("", views.YouTubeShortsDataView.as_view(), name="youtube-shorts-data"),
]
