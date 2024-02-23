"""
Serializers for the Domain APIs.
"""

from core.models import Click, Domain
from rest_framework import serializers


class ClickSerializer(serializers.ModelSerializer):
    """
    Serializer for the click object.
    """

    class Meta:
        """
        Meta class for the click
        """

        model = Click
        fields = [
            "id",
            "click_location",
            "click_type",
            "click_time",
        ]
        read_only_fields = ["id"]


class DomainSerializer(serializers.ModelSerializer):
    """
    Serializer for the domain object.
    """

    clicks = ClickSerializer(many=True, required=False)

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
            "clicks",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {"user": {"read_only": True}}

    def _create_clicks(self, clicks: list, domain: Domain) -> None:
        """
        Create clicks for a domain
        """
        # Get authenticated user.
        auth_user = self.context["request"].user
        for click in clicks:
            click_obj = Click.objects.create(user=auth_user, domain=domain, **click)
            domain.clicks.add(click_obj)

    def create(self, validated_data: dict) -> Domain:
        """
        Create a new domain.
        """
        clicks = validated_data.pop("clicks", [])
        domain = Domain.objects.create(**validated_data)
        self._create_clicks(clicks, domain)
        return domain

    def update(self, instance: Domain, validated_data: dict) -> Domain:
        """
        Update a domain.
        """
        clicks: list = validated_data.pop("clicks", [])

        if clicks is not None:
            instance.clicks.clear()
            self._create_clicks(clicks, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class DomainDetailSerializer(DomainSerializer):
    """
    Serialize a domain detail
    """

    class Meta(DomainSerializer.Meta):
        """
        Meta class for the domain detail
        """

        fields = DomainSerializer.Meta.fields + ["clicks"]
        read_only_fields = DomainSerializer.Meta.read_only_fields + ["clicks"]
