"""
Host URL Configuration
"""

from django.urls import include, path
from host import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("hosts", views.HostViewSet)

app_name = "host"

urlpatterns = [
    path("", include(router.urls)),
]
