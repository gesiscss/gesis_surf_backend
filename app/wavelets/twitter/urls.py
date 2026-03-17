"""
URLs for the Twitter app.
"""

from wavelets.twitter import views
from django.urls import path

app_name = "twitter"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.TwitterDataView.as_view(), name="twitter-data"),
]
