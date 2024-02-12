"""
Serializer for the window app
"""

from rest_framework import serializers

from core.models import Window


class WindowSerializer(serializers.ModelSerializer):
    """
    Serializer for the window object.
    """

    class Meta:
        """
        Meta class for the window serializer.
        """

        model = Window
        fields = (
            "id",
            "start_time",
            "closing_time",
            "created_at",
            "user",
        )
        read_only_fields = ("id",)
        extra_kwargs = {"user": {"read_only": True}}
