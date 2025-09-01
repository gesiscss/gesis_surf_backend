"""
Serializers for the GlobalSession model.
"""
from core.models import GlobalSession
from rest_framework import serializers

class GlobalSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalSession
        fields = [
            "id",
            "user",
            "start_time",
            "closing_time",
            "global_session_id"
        ]
        read_only_fields = [
            "id",
        ]
        extra_kwargs = {
            "user": {"read_only": True}
        }