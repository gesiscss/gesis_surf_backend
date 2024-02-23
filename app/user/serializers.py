"""
Serializers for the user API views.
"""

from core import models
from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class WaveSerializer(serializers.ModelSerializer):
    """
    Serializer for the wave object.
    """

    class Meta:
        """
        Meta class for the wave serializer.
        """

        model = models.Wave
        fields = (
            "id",
            "start_date",
            "end_date",
            "created_at",
            "wave_status",
            "wave_type",
            "wave_number",
            "client_id",
        )
        read_only_fields = ("id",)


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the user object GESIS.
    """

    waves = WaveSerializer(many=True, read_only=True, required=False)

    class Meta:
        """
        Meta class for the user serializer.
        """

        model = get_user_model()
        fields = ("user_id", "password", "waves")
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data):
        """
        Create a new user with encrypted password and return it.
        """
        waves = validated_data.pop("waves", [])
        user = get_user_model().objects.create_user(**validated_data)
        for wave in waves:
            user.waves.add(wave)
        return user

    def update(self, instance, validated_data):
        """
        Update a user, setting the password correctly and return it.
        """
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


# pylint: disable=W0223
# Check the issue here: https://shorturl.at/hwzZ5
class AuthTokenSerializer(serializers.Serializer):
    """
    Serializer for the user authentication object.
    """

    user_id = serializers.CharField()
    password = serializers.CharField(
        style={"input_type": "password"},
        trim_whitespace=False,
    )

    def validate(self, attrs) -> dict:
        """
        Validate and authenticate the user.
        """
        user_id = attrs.get("user_id")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            username=user_id,
            password=password,
        )
        if not user:
            message = _("Unable to authenticate with provided credentials")
            raise serializers.ValidationError(message, code="authentication")

        attrs["user"] = user
        return attrs
