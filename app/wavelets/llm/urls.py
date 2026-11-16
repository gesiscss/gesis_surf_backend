"""
URLs for the LLM wavelet API.
"""

from django.urls import path
from wavelets.llm import views

app_name = "llm"  # pylint: disable=invalid-name

urlpatterns = [
    path("", views.LLMDataView.as_view(), name="llm-data"),
]
