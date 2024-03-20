"""
Host URL Configuration
"""

from django.urls import include, path
from host import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("hosts", views.HostViewSet)

app_name = "host"

# urlpatterns = [
#     path("", include(router.urls)),
#     path(
#         "host/<str:hostname>/create/",
#         views.HostViewSet.as_view({"post": "create"}),
#         name="create",
#     ),
# ]

urlpatterns = [
    path("", include(router.urls)),
]
