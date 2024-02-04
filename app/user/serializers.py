"""
Serializers for the user API views.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the user object.
    """

    class Meta:
        """
        Meta class for the user serializer.
        """

        model = get_user_model()
        fields = ("user_id", "password")
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data):
        """
        Create a new user with encrypted password and return it.
        """
        return get_user_model().objects.create_user(**validated_data)
