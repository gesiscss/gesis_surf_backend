"""Selector URL Configuration"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from selector import views

router = DefaultRouter()
router.register("selectors", views.SelectorViewSet)

app_name = "selector"

urlpatterns = [
    path("", include(router.urls)),
    path(
        "task-result/<str:task_id>/",
        views.SelectorViewSet.as_view({"get": "get_async_task_result"}),
    ),
]
