"""
URLs for the global session app
"""

from django.urls import include, path
from globalsession import views
from rest_framework.routers import DefaultRouter

router: DefaultRouter = DefaultRouter()
router.register("global-session", views.GlobalSessionViewSet)

app_name = "globalsession"

urlpatterns: list = [
    path("", include(router.urls)),
]
