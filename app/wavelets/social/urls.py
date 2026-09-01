"""
URL configuration for the social wavelets API.
"""

from django.urls import path
from wavelets.social import views

app_name = "social"

urlpatterns = [
    path("", views.SocialPostView.as_view(), name="social-post"),
]
