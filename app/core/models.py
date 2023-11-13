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
