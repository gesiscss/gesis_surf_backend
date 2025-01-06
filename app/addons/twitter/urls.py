"""
URLs for the Twitter app.
"""

from addons.twitter import views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("twitter", views.TwitterDataView, basename="twitter")

app_name = "twitter"  # pylint: disable=invalid-name

urlpatterns = [
    path("", include(router.urls)),
]
