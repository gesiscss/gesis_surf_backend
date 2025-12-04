"""
URLs for the scroll app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from scrolls import views

router = DefaultRouter()
router.register("scrolls", views.ScrollViewSet, basename="scroll")

app_name = "scrolls"

urlpatterns = [
    path("", include(router.urls)),
]
