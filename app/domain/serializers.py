"""
Serializers for the Domain APIs.
"""

from core.models import Click, Domain, Scroll
from rest_framework import serializers


class ScrollSerializer(serializers.ModelSerializer):
    """
    Serializer for the scroll object.
    """

    class Meta:
        """
        Meta class for the scroll
        """

        model = Scroll
        fields = [
            "id",
            "scroll_x",
            "scroll_y",
            "page_x_offset",
            "page_y_offset",
            "scroll_time",
        ]
        read_only_fields = ["id"]


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


class DomainSingleSerializer(serializers.ModelSerializer):
    """
    Serializer for the domain object.
    """

    clicks = ClickSerializer(many=True, required=False)
    scrolls = ScrollSerializer(many=True, required=False)

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
            "scrolls",
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
        clicks: list = validated_data.pop("clicks", None)

        # Update or delete existing clicks
        if clicks is not None:
            for click in clicks:
                click_id = click.get("id", None)
                if click_id:
                    click_obj = Click.objects.get(id=click_id)
                    click_obj.click_location = click.get(
                        "click_location", click_obj.click_location
                    )
                    click_obj.click_type = click.get("click_type", click_obj.click_type)
                    click_obj.click_time = click.get("click_time", click_obj.click_time)
                    click_obj.save()
                else:
                    self._create_clicks([click], instance)
        # Update the domain
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class DomainDetailSerializer(DomainSingleSerializer):
    """
    Serialize a domain detail
    """

    class Meta(DomainSingleSerializer.Meta):
        """
        Meta class for the domain detail
        """

        fields = DomainSingleSerializer.Meta.fields + ["clicks"]
        read_only_fields = DomainSingleSerializer.Meta.read_only_fields + ["clicks"]
