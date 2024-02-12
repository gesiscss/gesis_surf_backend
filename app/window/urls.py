"""
URLs for the window app
"""

from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from window import views

router = DefaultRouter()
router.register("windows", views.WindowViewSet)

app_name = "window"

urlpatterns = [
    path("", include(router.urls)),
]
