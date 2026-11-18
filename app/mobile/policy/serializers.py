"""
Serializers for the mobile policy API.
"""

from rest_framework import serializers


class PolicyAppSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for one app of the allow-list.
    """

    package = serializers.CharField()
    tier = serializers.CharField()
    category = serializers.CharField()


class MobilePolicySerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for the mobile policy: the active release plus the user's
    data collection flag. The keys are the contract with the mobile app.
    """

    schema_version = serializers.IntegerField()
    policy_version = serializers.CharField()
    policy_hash = serializers.CharField()
    issued_at = serializers.CharField()
    data_collection = serializers.BooleanField()
    default_tier = serializers.CharField()
    apps = PolicyAppSerializer(many=True)
