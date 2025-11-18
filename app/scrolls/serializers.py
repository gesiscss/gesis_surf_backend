"""
Serializers for scroll app.
"""

from core.models import Domain, Scroll
from rest_framework import serializers


class ScrollSerializer(serializers.ModelSerializer):
    """
    Serializer for the scroll object.
    """

    domain_id = serializers.UUIDField(write_only=True, required=True)

    class Meta:  # type: ignore
        """
        Meta class for the scroll
        """

        model = Scroll
        fields: list = [
            "id",
            "user",
            "domain",
            "domain_id",
            "scroll_x",
            "scroll_y",
            "page_x_offset",
            "page_y_offset",
            "scroll_time",
        ]
        read_only_fields: list = ["id", "user", "domain", "created_at"]

    def create(self, validated_data: dict) -> Scroll:
        """
        Create and return a new Scroll instance.
        """
        domain_id = validated_data.pop("domain_id")
        domain = Domain.objects.get(id=domain_id, user=self.context["request"].user)

        return Scroll.objects.create(
            user=self.context["request"].user, domain=domain, **validated_data
        )
