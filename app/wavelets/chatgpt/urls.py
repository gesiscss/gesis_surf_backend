"""
URLs for the chatgpt addon.
"""

from django.urls import path
from wavelets.chatgpt import views

app_name = "chatgpt"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.ChatGPTDataView.as_view(), name="chatgpt-data"),
]
