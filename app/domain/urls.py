"""
URLs for the domain app
"""

from django.urls import include, path
from domain import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("domains", views.DomainViewSet)
router.register("clicks", views.ClickViewSet)

app_name = "domain"

urlpatterns = [
    path("", include(router.urls)),
]
