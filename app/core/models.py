"""
This file is used to create models for the core app.
"""

import uuid
from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.conf import settings


class UserManager(BaseUserManager):
    """
    User manager class for the users .
    """

    def create_user(
        self,
        user_id: str,
        password: Any = None,
        **extra_fields: Any,
    ) -> "User":
        """
        Creates and saves a new user with a generated GESIS user_id.

        Args:
            user_id (str): The id of the user from GESIS.
            extra_fields (dict): Extra fields to be saved.

        Returns:
            object: The created user instance.
        """
        if not user_id:
            raise ValueError("Users must have an user_id")
        user = self.model(user_id=user_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        user_id: str,
        password: Any,
        **extra_fields: Any,
    ) -> "User":
        """
        Creates and saves a new superuser with the given GESIS user_id.

        Args:
            user_id (str): The id of the user from GESIS.
            token_gesis (Any): The token of the user from GESIS.

        Returns:
            object: The created superuser instance.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(user_id, password, **extra_fields)


class User(
    AbstractBaseUser,
    PermissionsMixin,
):
    """
    Custom participant model.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, blank=False
    )
    user_id = models.CharField(max_length=32, unique=True, blank=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    waves = models.ManyToManyField("Wave")

    objects = UserManager()

    USERNAME_FIELD = "user_id"


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

    def __str__(self) -> str:
        """
        Returns the string representation of the wave.

        Returns:
            str: A formatted string with wave information.
        """

        return f"{self.start_date} to {self.end_date}"


class Window(models.Model):
    """
    Custom window model.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, blank=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="windows",
    )
    start_time = models.DateTimeField(blank=True)
    closing_time = models.DateTimeField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=False)

    def __str__(self) -> str:
        """
        Returns the string representation of the window.

        Returns:
            str: A formatted string with window information.
        """

        return f"{self.start_time} to {self.closing_time}"
