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
        ]
        read_only_fields = ["id"]


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the category object.
    """

    criteria = CriteriaSerializer()

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

    def _create_criteria(self, categories_data: list) -> None:
        """
        Create criteria for the host.
        """
        for category_data in categories_data:
            criteria_data = category_data.pop("criteria")
            criteria = Criteria.objects.create(**criteria_data)
            Category.objects.create(criteria=criteria, **category_data)

    def create(self, validated_data):
        """
        Create a new host and return it.
        """
        categories_data = validated_data.pop("categories")
        self._create_criteria(categories_data)
        return Host.objects.create(**validated_data)
