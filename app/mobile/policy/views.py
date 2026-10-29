"""
Views for the mobile policy API.
"""

from datetime import timezone as dt_timezone
from typing import Any

from core.models import MobileClient, MobilePolicyRelease
from django.utils import timezone
from django.utils.http import parse_etags
from drf_spectacular.utils import OpenApiParameter, extend_schema
from mobile.policy import serializers
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

# Query parameter -> (MobileClient field, maximum length)
TELEMETRY_PARAMETERS = {
    "app_version": ("app_version", 32),
    "platform": ("platform", 32),
    "policy_version": ("last_policy_version", 32),
    "policy_source": ("last_policy_source", 16),
}


def build_etag(policy_hash: str, data_collection: bool) -> str:
    """
    Builds the ETag from everything that varies in the response: the release
    and the user's data collection flag, so a change of the flag is never
    answered with 304.
    """
    return f'"{policy_hash}-dc{int(data_collection)}"'


def etag_matches(if_none_match: str | None, etag: str) -> bool:
    """
    Tells whether the If-None-Match header matches the ETag (weak comparison,
    as proxies may turn a strong ETag into a weak one).
    """
    if not if_none_match:
        return False
    tags = [tag.removeprefix("W/") for tag in parse_etags(if_none_match)]
    return "*" in tags or etag in tags


def format_issued_at(release: MobilePolicyRelease) -> str:
    """
    Formats the publication time of the release as UTC with a Z suffix.
    """
    return release.created_at.astimezone(dt_timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_telemetry(client: MobileClient, params: Any) -> None:
    """
    Stores what the app reports about itself. Nothing depends on these values.
    A bulk update is used so that every poll does not add a history row.
    """
    values: dict[str, Any] = {"last_seen_at": timezone.now()}
    for parameter, (field, max_length) in TELEMETRY_PARAMETERS.items():
        value = params.get(parameter, "").strip()[:max_length]
        if value:
            values[field] = value
    MobileClient.objects.filter(pk=client.pk).update(  # pylint: disable=no-member
        **values
    )


class MobilePolicyView(APIView):
    """
    API view for the mobile app allow-list policy.
    """

    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = serializers.MobilePolicySerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name=name, type=str, required=False)
            for name in TELEMETRY_PARAMETERS
        ],
        responses={200: serializers.MobilePolicySerializer, 304: None, 404: None},
    )
    def get(self, request: Request) -> Response:
        """
        Return the active release with the user's data collection flag, or 304
        when the app already holds exactly this response.
        """
        release = MobilePolicyRelease.objects.filter(  # pylint: disable=no-member
            is_active=True
        ).first()
        if release is None:
            return Response(
                {"detail": "No active mobile policy release."},
                status=status.HTTP_404_NOT_FOUND,
            )

        client, _ = MobileClient.objects.get_or_create(  # pylint: disable=no-member
            user=request.user
        )
        record_telemetry(client, request.query_params)

        etag = build_etag(release.policy_hash, client.data_collection)
        if etag_matches(request.headers.get("If-None-Match"), etag):
            return Response(status=status.HTTP_304_NOT_MODIFIED, headers={"ETag": etag})

        data = {
            "schema_version": release.payload["schema_version"],
            "policy_version": release.version,
            "policy_hash": release.policy_hash,
            "issued_at": format_issued_at(release),
            "data_collection": client.data_collection,
            "default_tier": release.payload["default_tier"],
            "apps": release.payload["apps"],
        }
        return Response(
            self.serializer_class(data).data,
            headers={"ETag": etag},
        )
