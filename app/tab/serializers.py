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

    # Scoped per-request in __init__ (BOLA: a queryset of all domains let
    # any participant attach another participant's domain to their tab).
    domain_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Domain.objects.none(),
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

    def __init__(self, *args, **kwargs):
        """
        Scope the attachable domains to the requesting user (audit P0 #1).

        domain_ids is a many=True related field: the queryset that
        validates submitted IDs lives on the child_relation, not on the
        list wrapper.
        """
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            self.fields["domain_ids"].child_relation.queryset = (
                Domain.objects.filter(user=request.user)
            )

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

        Only domains owned by the tab's user can be attached (BOLA
        ownership guard, belt-and-suspenders for the domain_ids scoping).
        """
        if domains and hasattr(domains[0], "id"):
            for domain in domains:
                if domain.user_id != tab.user_id:
                    continue
                tab.domains.add(domain)
        else:
            self._create_domains(domains, tab)

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

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if domains is not None:
            # instance.domains.clear()
            self._handle_domains(domains, instance)

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
