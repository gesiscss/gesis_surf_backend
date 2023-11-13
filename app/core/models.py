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


class UserManager(BaseUserManager):
    """
    User manager class.
    """

    def create_user(self, is_active: bool = True, **extra_fields: dict) -> object:
        """
        Creates and saves a new user just with a random Token.
        """
        token = self.generate_token()
        user = self.model(token=token, is_active=is_active, **extra_fields)
        user.save(using=self._db)
        return user

    def create_superuser(self, **extra_fields: dict) -> object:
        """
        Creates and saves a new superuser.
        """
        user = self.create_user(**extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

    @staticmethod
    def generate_token() -> str:
        """
        Generates a random token.
        """
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for i in range(32))


class Participant(AbstractBaseUser, PermissionsMixin):
    """
    Custom participant model.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=32, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "token"

    def __str__(self) -> str:
        """
        Returns the string representation of the user.
        """
        return self.token


class Wave(models.Model):
    """
    Custom wave model.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    client_id = models.CharField(max_length=32)
    wave_number = models.IntegerField()
    wave_name = models.CharField(max_length=32)
    wave_type = models.CharField(max_length=32)
    wave_status = models.CharField(max_length=32)
    participants = models.ManyToManyField(Participant, through="WaveParticipant")

    def __str__(self) -> str:
        return f"{self.client_id} - {self.wave_number} - {self.start_date} to {self.end_date}"


class WaveParticipant(models.Model):
    """
    Custom wave participant model.
    """

    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    wave = models.ForeignKey(Wave, on_delete=models.CASCADE)
    addtional_field = models.CharField(max_length=32)
