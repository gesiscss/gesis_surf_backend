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
    path(
        "task-result/<str:task_id>/",
        views.HostViewSet.as_view({"get": "get_async_task_result"}),
    ),
]
