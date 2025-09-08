"""
URLs for the clicks app.
"""

from clicks import views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("", views.ClickViewSet, basename="click")

app_name = "click"

urlpatterns = [
    path("", include(router.urls)),
]
