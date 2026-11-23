"""
Views for the mobile events API.
"""

from core.mixins.maintenance_mixins import MaintenanceModeMixin
from core.models import MobileClient, MobilePolicyRelease
from drf_spectacular.utils import extend_schema
from elasticsearch.exceptions import TransportError
from mobile.capture import ingest, serializers
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class MobileEventsView(MaintenanceModeMixin, APIView):
    """
    API view for the accessibility and VPN events of the mobile app.
    """

    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = serializers.EventBatchSerializer

    @extend_schema(
        request=serializers.EventBatchSerializer,
        responses={201: serializers.EventResultSerializer, 400: None, 403: None},
    )
    def post(self, request: Request) -> Response:
        """
        Store the events in the monthly indexes. Returns 201 when at least one
        event was stored or was already stored, 403 when data collection is
        switched off for the user and 503 when the upload should be retried.
        """
        mobile_client, _ = (
            MobileClient.objects.get_or_create(  # pylint: disable=no-member
                user=request.user
            )
        )
        if not mobile_client.data_collection:
            return Response(
                {"detail": "Data collection is switched off for this user."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        release = MobilePolicyRelease.objects.filter(  # pylint: disable=no-member
            is_active=True
        ).first()
        if release is None:
            return Response(
                {"detail": "No active mobile policy release."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        categories = {
            app["package"]: app["category"] for app in release.payload["apps"]
        }

        data = serializer.validated_data
        try:
            result = ingest.ingest_events(
                str(request.user.user_id),  # type: ignore[union-attr]
                data["module"],
                data["events"],
                dict(data.get("client", {})),
                categories,
            )
        except TransportError:
            return Response(
                {"detail": "The events could not be stored, please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if result["accepted"] + result["duplicates"] == 0:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_201_CREATED)
