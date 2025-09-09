"""
URLs for the domain app
"""

from django.urls import include, path
from domain import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("domains", views.DomainViewSet)
# router.register("clicks", views.ClickViewSet)
# router.register("scrolls", views.ScrollViewSet)

app_name = "domain"

urlpatterns = [
    path("", include(router.urls)),
]
