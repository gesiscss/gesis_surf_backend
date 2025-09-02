"""
Serializers for the window APIs.
"""

from core.models import Window
from rest_framework import serializers


class WindowSerializer(serializers.ModelSerializer):
    """
    Serializer for the window object.
    """

    class Meta:
        """
        Meta class for the window serializer.
        """

        model = Window
        fields = [
            "id",
            "user",
            "start_time",
            "closing_time",
            "window_num",
            "window_session_id",
            "global_session",
        ]

        # Able to change the fields, but not the id.
        read_only_fields = ["id"]
        extra_kwargs = {"user": {"read_only": True}}


class WindowDetailSerializer(WindowSerializer):
    """
    Serializer for window detail view.
    """

    class Meta(WindowSerializer.Meta):
        """
        Meta class for the window detail serializer.
        """

        fields = WindowSerializer.Meta.fields + ["user"]
        read_only_fields = WindowSerializer.Meta.read_only_fields
