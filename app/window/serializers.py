"""
Serializers for the window APIs.
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
        fields = ["id", "start_time", "closing_time", "created_at"]

        # Able to change the fields, but not the id.
        read_only_fields = ["id"]
        extra_kwargs = {"user": {"read_only": True}}


# class WindowDetailSerializer(WindowSerializer):
#     """
#     Serialize a window detail.
#     """

#     class Meta(WindowSerializer.Meta):
#         """
#         Meta class for the window detail serializer.
#         """

#         fields = WindowSerializer.Meta.fields
