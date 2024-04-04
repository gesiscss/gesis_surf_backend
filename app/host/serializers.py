"""
Serializers for the host APIs.
"""

from core.models import Category, Criteria, Host
from rest_framework import serializers


class CriteriaSerializer(serializers.ModelSerializer):
    """
    Serializer for the criteria object.
    """

    class Meta:
        """
        Meta class for the criteria serializer.
        """

        model = Criteria
        fields = [
            "id",
            "criteria_classification",
            "criteria_window",
            "criteria_tab",
            "criteria_domain",
            "criteria_click",
            "criteria_scroll",
            "snapshot_html",
        ]
        read_only_fields = ["id"]


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the category object.
    """

    criteria = CriteriaSerializer(allow_null=True, required=False)

    class Meta:
        """
        Meta class for the category serializer.
        """

        model = Category
        fields = [
            "id",
            "category_score",
            "category_parent",
            "category_label",
            "category_confidence",
            "created_at",
            "criteria",
        ]
        read_only_fields = ["id"]


class HostSerializer(serializers.ModelSerializer):
    """
    Serializer for the host object.
    """

    categories = CategorySerializer(many=True, required=False)

    class Meta:
        """
        Meta class for the host serializer.
        """

        model = Host
        fields = [
            "id",
            "hostname",
            "created_at",
            "categories",
        ]
        read_only_fields = ["id"]

    def _create_criteria(self, criteria_data: dict) -> None:
        """
        Create criteria for the host.
        """
        criteria = Criteria.objects.create(**criteria_data)
        return criteria

    def _create_category(self, categories_data: list, host: Host) -> None:
        """
        Create categories for the host.
        """
        criteria_data = categories_data.pop("criteria", None)
        criteria = self._create_criteria(criteria_data) if criteria_data else None
        category = Category.objects.create(criteria=criteria, **categories_data)
        host.categories.add(category)

    def create(self, validated_data):
        """
        Create a new host and return it.
        """
        categories_data = validated_data.pop("categories", [])
        host = Host.objects.create(**validated_data)
        for category_data in categories_data:
            self._create_category(category_data, host)
        return host
