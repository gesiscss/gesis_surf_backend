"""
Serializers for the selector app.
"""

from core.models import SelectorConfig
from rest_framework import serializers


class SelectorConfigSerializer(serializers.ModelSerializer):
    """
    Serializer for the selector config object.
    """

    class Meta:
        """
        Meta class for the selector config serializer.
        """

        model = SelectorConfig
        fields = [
            "id",
            "family",
            "provider",
            "version",
            "hostname_patterns",
            "selectors",
            "is_active",
            "updated_at",
        ]
        read_only_fields = ["id"]
