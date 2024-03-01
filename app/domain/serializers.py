"""
Serializers for the Domain APIs.
"""

from core.models import Click, Domain, Scroll, User
from rest_framework import serializers


class ScrollSerializer(serializers.ModelSerializer):
    """
    Serializer for the scroll object.
    """

    class Meta:
        """
        Meta class for the scroll
        """

        model: Scroll = Scroll
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

    class Meta:
        """
        Meta class for the click
        """

        model: Click = Click
        fields: list = [
            "id",
            "click_location",
            "click_type",
            "click_time",
        ]
        read_only_fields: list = ["id"]


class DomainSingleSerializer(serializers.ModelSerializer):
    """
    Serializer for the domain object.
    """

    clicks: ClickSerializer = ClickSerializer(many=True, required=False)
    scrolls: ScrollSerializer = ScrollSerializer(many=True, required=False)

    class Meta:
        """
        Meta class for the domain
        """

        model: list = Domain
        fields: list = [
            "id",
            "domain_title",
            "domain_url",
            "domain_fav_icon",
            "domain_status",
            "clicks",
            "scrolls",
        ]
        read_only_fields: list = ["id"]
        extra_kwargs: dict = {"user": {"read_only": True}}

    def _create_clicks(self, clicks: list, domain: Domain) -> None:
        """
        Create clicks for a domain
        """
        # Get authenticated user.
        auth_user: User = self.context["request"].user
        for click in clicks:
            click_obj: Click = Click.objects.create(
                user=auth_user, domain=domain, **click
            )
            domain.clicks.add(click_obj)

    def _create_scrolls(self, scrolls: list, domain: Domain) -> None:
        """
        Create scrolls for a domain
        """
        # Get authenticated user.
        auth_user: User = self.context["request"].user
        for scroll in scrolls:
            scroll_obj: Scroll = Scroll.objects.create(
                user=auth_user, domain=domain, **scroll
            )
            domain.scrolls.add(scroll_obj)

    def create(self, validated_data: dict) -> Domain:
        """
        Create a new domain.
        """
        clicks = validated_data.pop("clicks", [])
        scrolls = validated_data.pop("scrolls", [])
        domain = Domain.objects.create(**validated_data)
        self._create_clicks(clicks, domain)
        self._create_scrolls(scrolls, domain)

        return domain

    def update(self, instance: Domain, validated_data: dict) -> Domain:
        """
        Update a domain.
        """
        clicks: list = validated_data.pop("clicks", None)
        scrolls: list = validated_data.pop("scrolls", None)

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

        # Update or delete existing scrolls
        if scrolls is not None:
            for scroll in scrolls:
                scroll_id = scroll.get("id", None)
                if scroll_id:
                    scroll_obj = Scroll.objects.get(id=scroll_id)
                    scroll_obj.scroll_x = scroll.get("scroll_x", scroll_obj.scroll_x)
                    scroll_obj.scroll_y = scroll.get("scroll_y", scroll_obj.scroll_y)
                    scroll_obj.page_x_offset = scroll.get(
                        "page_x_offset", scroll_obj.page_x_offset
                    )
                    scroll_obj.page_y_offset = scroll.get(
                        "page_y_offset", scroll_obj.page_y_offset
                    )
                    scroll_obj.scroll_time = scroll.get(
                        "scroll_time", scroll_obj.scroll_time
                    )
                    scroll_obj.save()
                else:
                    self._create_scrolls([scroll], instance)

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
