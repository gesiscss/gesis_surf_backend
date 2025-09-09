"""
Serializer for the Click model.
"""

from core.models import Click, Domain
from rest_framework import serializers


class ClickSerializer(serializers.ModelSerializer):
    """
    Serializer for the Click model.
    """

    domain_id = serializers.UUIDField(write_only=True, required=True)

    class Meta:  # type: ignore
        model = Click
        fields = [
            "id",
            "user",
            "domain",
            "domain_id",
            "click_time",
            "click_type",
            "click_page_x",
            "click_page_y",
            "click_target_element",
            "click_target_tag",
            "click_target_id",
            "click_target_class",
            "click_referrer",
            "created_at",
        ]
        read_only_fields = ["id", "user", "domain", "created_at"]

    def create(self, validated_data: dict) -> Click:
        """
        Create and return a new Click instance.
        """
        domain_id = validated_data.pop("domain_id")
        domain = Domain.objects.get(id=domain_id, user=self.context["request"].user)

        return Click.objects.create(
            user=self.context["request"].user, domain=domain, **validated_data
        )
