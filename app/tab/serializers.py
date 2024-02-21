"""
Serializers for the Tab APIs.
"""

from rest_framework import serializers

from core.models import Domain
from core.models import Tab


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


class TabSerializer(serializers.ModelSerializer):
    """
    Serializer for the tab object.
    """

    domains = DomainSerializer(many=True, required=False)

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
            "domains",
        ]

        # Able to change the fields, but not the id.
        read_only_fields = ["id"]
        extra_kwargs = {"user": {"read_only": True}}

    def _create_domains(self, domains: list, tab: Tab) -> None:
        """
        Create the domain objects.
        """
        # Getting authenticated user.
        auth_user = self.context["request"].user
        for domain in domains:
            domain_obj = Domain.objects.create(user=auth_user, **domain)
            tab.domains.add(domain_obj)

    def create(self, validated_data):
        """
        Create a new tab even with duplicated domains.
        """
        domains = validated_data.pop("domains", [])
        tab = Tab.objects.create(**validated_data)
        self._create_domains(domains, tab)
        return tab

    def update(self, instance: Tab, validated_data: dict) -> Tab:
        """
        Update the tab object.
        """
        domains: list = validated_data.pop("domains", None)

        if domains is not None:
            instance.domains.clear()
            self._create_domains(domains, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


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
