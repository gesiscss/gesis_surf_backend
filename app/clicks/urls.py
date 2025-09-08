"""
URLs for the clicks app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from clicks import views

router = DefaultRouter()
router.register("", views.ClickViewSet, basename="click")

app_name = "click"

urlpatterns = [
    path("", include(router.urls)),
]
