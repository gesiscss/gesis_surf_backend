"""
Serializers for the Tab APIs.
"""

from rest_framework import serializers

from core.models import Tab


class TabSerializer(serializers.ModelSerializer):
    """
    Serializer for the tab object.
    """

    class Meta:
        """
        Meta class for the tab
        """

        model = Tab
        fields = [
            "id",
            "start_time",
            "closing_time",
            "created_at",
            "snapshot_html",
            "tab_id",
            "window_num",
        ]

        # Able to change the fields, but not the id.
        read_only_fields = ["id"]
        extra_kwargs = {"user": {"read_only": True}}
