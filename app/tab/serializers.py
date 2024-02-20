"""
Serializers for the Tab APIs.
"""

from rest_framework import serializers

from core.models import Domain
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
            "tab_num",
            "window_num",
        ]

        # Able to change the fields, but not the id.
        read_only_fields = ["id"]
        extra_kwargs = {"user": {"read_only": True}}


class TabDetailSerializer(TabSerializer):
    """
    Serializer for tab detail view.
    """

    class Meta(TabSerializer.Meta):
        """
        Meta class for the tab
        """

        fields = TabSerializer.Meta.fields + ["user"]
        read_only_fields = TabSerializer.Meta.read_only_fields


class DomainSerializer(serializers.ModelSerializer):
    """
    Serializer for the domain object.
    """

    class Meta:
        """
        Meta class for the domain
        """

        model = Domain
        fields = [
            "id",
            "domain_title",
            "domain_url",
            "domain_fav_icon",
            "domain_status",
        ]
        read_only_fields = ["id"]
