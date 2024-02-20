"""
URLs for the tab app
"""

from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from tab import views

router = DefaultRouter()
router.register("tabs", views.TabViewSet)
router.register("domains", views.DomainViewSet)


app_name = "tab"

urlpatterns = [
    path("", include(router.urls)),
]
