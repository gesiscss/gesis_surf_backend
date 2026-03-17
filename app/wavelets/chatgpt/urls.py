"""
URLs for the chatgpt addon.
"""

from wavelets.chatgpt import views
from django.urls import path

app_name = "chatgpt"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.ChatGPTDataView.as_view(), name="chatgpt-data"),
]
