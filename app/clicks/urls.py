"""
URLs for the clicks app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from clicks import views

router = DefaultRouter()
router.register("clicks", views.ClickViewSet)

app_name = "clicks"

urlpatterns = [
    path("", include(router.urls)),
]
