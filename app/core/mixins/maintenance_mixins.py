from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer


class MaintenanceModeMixin:
    """
    Mixin for maintenance mode.
    """

    maintenance_message = {
        "detail": "Service temporarily unavailable, please try again later."
    }

    def dispatch(self, request, *args, **kwargs) -> Response:
        """
        Dispatch method for maintenance mode.
        """
        if self.is_maintenance_mode():
            response = Response(
                self.maintenance_message,
                status=status.HTTP_200_OK,
            )
            response.accepted_renderer = JSONRenderer()
            response.accepted_media_type = "application/json"
            response.renderer_context = {}
            return response
        return super().dispatch(request, *args, **kwargs)

    def is_maintenance_mode(self) -> bool:
        """
        Check if maintenance mode is enabled.
        """
        return getattr(settings, "MAINTENANCE_MODE", False)
