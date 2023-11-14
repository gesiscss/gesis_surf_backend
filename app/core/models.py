"""
This file is used to create models for the core app.
"""

import secrets
import string
import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from typing import Dict, Any


class UserManager(BaseUserManager):
    """
    User manager class.
    """

    def create_user(
        self, token, password=None, is_active: bool = True, **extra_fields: Any
    ) -> "Participant":
        """
        Creates and saves a new user just with a random Token.

        Args:
            is_active (bool): User is active or not.
            extra_fields (dict): Extra fields to be saved.

        Returns:
            object: The created user instance.
        """
        # token = self.generate_token()
        user = self.model(token=token, is_active=is_active, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        token,
        password,
        **extra_fields: Any,
    ) -> "Participant":
        """
        Creates and saves a new superuser.

        Args:
            extra_fields (dict): Extra fields to be saved.

        Returns:
            object: The created superuser instance.
        """
        user = self.create_user(token, password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user

    @staticmethod
    def generate_token() -> str:
        """
        Generates a random token.

        Returns:
            str: The generated token.
        """
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for i in range(32))


class Participant(AbstractBaseUser, PermissionsMixin):
    """
    Custom participant model.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, blank=False
    )
    token = models.CharField(max_length=32, unique=True, blank=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "token"

    def __str__(self) -> str:
        """
        Returns the string representation of the participant.

        Returns:
            str: The token of the participant.
        """
        return str(self.token)


class WaveParticipant(models.Model):
    """
    Custom wave participant model.
    """

    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    wave = models.ForeignKey("Wave", on_delete=models.CASCADE)
    additional_field = models.CharField(max_length=32)


class Wave(models.Model):
    """
    Custom wave model.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, blank=False
    )
    start_date = models.DateTimeField(blank=False)
    end_date = models.DateTimeField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=False)
    client_id = models.CharField(max_length=32, blank=False)
    wave_number = models.IntegerField(blank=False)
    wave_name = models.CharField(max_length=32, blank=False)
    wave_type = models.CharField(max_length=32, blank=False)
    wave_status = models.CharField(max_length=32, blank=False)
    participants = models.ManyToManyField(Participant, through="WaveParticipant")

    def __str__(self) -> str:
        """
        Returns the string representation of the wave.

        Returns:
            str: A formatted string with wave information.
        """

        return f"{self.client_id} - {self.wave_number} - {self.start_date} to {self.end_date}"
