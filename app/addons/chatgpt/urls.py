"""
URLs for the chatgpt addon.
"""

from addons.chatgpt import views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("chatgpt", views.ChatGPTDataView, basename="chatgpt")

app_name = "chatgpt"  # pylint: disable=invalid-name

urlpatterns = [
    path("", include(router.urls)),
]
