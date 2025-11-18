"""
URLs for the scroll app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from scrolls import views

router = DefaultRouter()
router.register("", views.ScrollViewSet, basename="scroll")

app_name = "scroll"

urlpatterns = [
    path("", include(router.urls)),
]
