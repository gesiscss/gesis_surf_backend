"""
Serializers for the GlobalSession model.
"""

from typing import Any

from core.models import GlobalSession
from rest_framework import serializers


class GlobalSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model: type[GlobalSession] = GlobalSession
        fields: list[str] = [
            "id",
            "user",
            "start_time",
            "closing_time",
            "global_session_id",
        ]
        read_only_fields: list[str] = [
            "id",
        ]
        extra_kwargs: dict[str, Any] = {"user": {"read_only": True}}
