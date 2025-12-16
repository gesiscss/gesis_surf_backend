"""
Serializers for the Domain APIs.
"""

from core.models import Click, Domain, Scroll
from domain.tasks import process_domain_snapshot_task
from rest_framework import serializers


class ScrollSerializer(serializers.ModelSerializer):
    """
    Serializer for the scroll object.
    """

    class Meta:  # type: ignore
        """
        Meta class for the scroll
        """

        model = Scroll
        fields: list = [
            "id",
            "scroll_x",
            "scroll_y",
            "page_x_offset",
            "page_y_offset",
            "scroll_time",
        ]
        read_only_fields: list = ["id"]


class ClickSerializer(serializers.ModelSerializer):
    """
    Serializer for the click object.
    """

    class Meta:  # type: ignore
        """
        Meta class for the click
        """

        model = Click
        fields: list = [
            "id",
            "click_time",
            "click_type",
            "click_target_element",
            "click_target_tag",
            "click_target_id",
            "click_target_class",
            "click_page_x",
            "click_page_y",
            "click_referrer",
        ]
        read_only_fields: list = ["id"]


class DomainSingleSerializer(serializers.ModelSerializer):
    """
    Serializer for the domain object.
    """

    # Relationships
    clicks: ClickSerializer = ClickSerializer(many=True, read_only=True)
    scrolls: ScrollSerializer = ScrollSerializer(many=True, read_only=True)

    snapshot_html = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )

    class Meta:  # type: ignore
        """
        Meta class for the domain
        """

        model = Domain
        fields: list = [
            "id",
            "start_time",
            "closing_time",
            "domain_title",
            "domain_url",
            "domain_fav_icon",
            "domain_last_accessed",
            "domain_session_id",
            "snapshot_html",
            "category_number",
            "criteria_classification",
            "category_label",
            "clicks",
            "scrolls",
        ]
        read_only_fields: list = ["id"]
        extra_kwargs: dict = {"user": {"read_only": True}}

    def _queue_snapshot_processing(self, domain_id: str, snapshot_html: str) -> None:
        """
        Queue the snapshot processing task.
        """

        process_domain_snapshot_task.apply_async(
            args=[str(domain_id), snapshot_html]
        )  # type: ignore[attr-defined]

    def create(self, validated_data: dict) -> Domain:
        """
        Create a new domain.
        """

        snapshot_html = validated_data.pop("snapshot_html", None)

        # pylint: disable=no-member
        domain = Domain.objects.create(**validated_data)

        if snapshot_html:

            self._queue_snapshot_processing(str(domain.id), snapshot_html)

        return domain

    def update(self, instance: Domain, validated_data: dict) -> Domain:
        """
        Update a domain.
        """

        snapshot_html = validated_data.pop("snapshot_html", None)

        # Update the domain
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if snapshot_html:
            self._queue_snapshot_processing(str(instance.id), snapshot_html)

        return instance


class DomainDetailSerializer(DomainSingleSerializer):
    """
    Serialize a domain detail
    """

    class Meta(DomainSingleSerializer.Meta):
        """
        Meta class for the domain detail
        """

        fields = DomainSingleSerializer.Meta.fields
        read_only_fields = DomainSingleSerializer.Meta.read_only_fields
