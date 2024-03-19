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
        fields = ["id", "hostname", "created_at", "categories"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        """
        Create a new host.
        """
        hostname = validated_data.pop("host")["hostname"]
        host, _ = Host.objects.get_or_create(hostname=hostname)
        categories_data = validated_data.pop("categories", [])
        for category_data in categories_data:
            criteria_data = category_data.pop("criteria")
            category, _ = Category.objects.get_or_create(host=host, **category_data)
            category.criteria = criteria_data
            category.save()
        return host
