"""
Serializers for the Tab APIs.
"""

from core.models import Domain, Tab
from rest_framework import serializers


class DomainSerializer(serializers.ModelSerializer):
    """
    Serializer for the domain object.
    """

    class Meta:  # type: ignore
        """
        Meta class for the domain
        """

        model = Domain
        fields = [
            "id",
            "user",
            "start_time",
            "closing_time",
            "domain_title",
            "domain_url",
            "domain_fav_icon",
            "domain_last_accessed",
            "snapshot_html",
            "category_number",
            "criteria_classification",
            "category_label",
            "domain_session_id",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {"user": {"read_only": True}}


class TabSerializer(serializers.ModelSerializer):
    """
    Serializer for the tab object.
    """

    domains = DomainSerializer(many=True, required=False)

    domain_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Domain.objects.all(),
        write_only=True,
        required=False,
        source="domains",
    )

    class Meta:  # type: ignore
        """
        Meta class for the tab
        """

        model = Tab
        fields = [
            "id",
            "user",
            "window",
            "start_time",
            "closing_time",
            "window_num",
            "tab_num",
            "tab_session_id",
            "domains",
            "domain_ids",
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

    def _handle_domains(self, domains: list, tab: Tab) -> None:
        """
        Handle the domains for the tab.
        """
        if domains and hasattr(domains[0], "id"):
            for domain in domains:
                tab.domains.add(domain)
        else:
            self._create_domains(domains, tab)

    def _update_domains(self, domain_updates: list, tab: Tab) -> None:
        """
        Update the domains for the tab.
        """
        auth_user = self.context["request"].user

        for domain_data in domain_updates:

            domain_id = domain_data.get("id")

            if domain_id:
                try:
                    domain = Domain.objects.get(id=domain_id, user=auth_user)
                    for attr, value in domain_data.items():
                        setattr(domain, attr, value)
                    domain.save()

                    if domain not in tab.domains.all():
                        tab.domains.add(domain)

                except Domain.DoesNotExist:
                    continue

    def create(self, validated_data):
        """
        Create a new tab even with duplicated domains.
        """
        domains = validated_data.pop("domains", [])
        tab = Tab.objects.create(**validated_data)

        # Hanlde domains if any
        if domains:
            self._handle_domains(domains, tab)

        return tab

    def update(self, instance: Tab, validated_data: dict) -> Tab:
        """
        Update the tab object.
        """
        domains: list = validated_data.pop("domains", None)
        domain_updates: list = validated_data.pop("domain_updates", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if domains is not None:
            instance.domains.clear()
            self._handle_domains(domains, instance)

        if domain_updates is not None:
            self._update_domains(domain_updates, instance)

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
