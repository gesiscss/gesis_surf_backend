"""
URLs for the Twitter app.
"""

from django.urls import path
from wavelets.twitter import views

app_name = "twitter"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.TwitterDataView.as_view(), name="twitter-data"),
]
