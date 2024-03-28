"""
Serializers for the user API views.
"""

from core import models
from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class PrivacySerializer(serializers.ModelSerializer):
    """
    Serializer for the privacy object.
    """

    class Meta:
        """
        Meta class for the privacy serializer.
        """

        model = models.Privacy
        fields = (
            "id",
            "privacy_mode",
            "privacy_start_time",
            "privacy_end_time",
        )
        read_only_fields = ("id",)


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

    waves = WaveSerializer(many=True, required=False)
    privacy = PrivacySerializer(required=True)

    class Meta:
        """
        Meta class for the user serializer.
        """

        model = get_user_model()
        fields = ("user_id", "password", "waves", "privacy")
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def to_representation(self, instance):
        """
        Serialize the user object with wave when exists.
        """
        ret = super().to_representation(instance)
        waves = models.Wave.objects.filter(users=instance)
        ret["waves"] = WaveSerializer(waves, many=True).data
        return ret

    def create(self, validated_data):
        """
        Create a new user with encrypted password and return it.
        """
        with transaction.atomic():
            waves = validated_data.pop("waves", [])
            privacy = validated_data.pop("privacy")
            user = get_user_model().objects.create_user(**validated_data)
            privacy = models.Privacy.objects.create(user=user, **privacy)
            for wave in waves:
                wave = models.Wave.objects.create(**wave)
                wave.users.add(user)
            return user

    def update(self, instance, validated_data):
        """
        Update a user, setting the password correctly and return it.
        """
        password = validated_data.pop("password", None)
        privacy = validated_data.pop("privacy", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        if privacy:
            user.privacy.privacy_mode = privacy.get(
                "privacy_mode", user.privacy.privacy_mode
            )
            user.privacy.privacy_start_time = privacy.get(
                "privacy_start_time", user.privacy.privacy_start_time
            )
            user.privacy.privacy_end_time = privacy.get(
                "privacy_end_time", user.privacy.privacy_end_time
            )
            user.privacy.save()

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
