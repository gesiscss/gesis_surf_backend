"""
This file is used to create models for the core app.
"""

import uuid
from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


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

    objects = UserManager()

    USERNAME_FIELD = "user_id"

    # class Meta:
    #     """
    #     Meta class for the participant model.
    #     """

    #     verbose_name = "Participant"
    #     verbose_name_plural = "Participants"

    # def __str__(self) -> str:
    #     """

    #     Returns the string representation of the participant.

    #     Returns:
    #         str: The token of the participant.
    #     """
    #     return str(self.user_id)


# class WaveParticipant(models.Model):
#     """
#     Custom wave participant model.
#     """

#     participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
#     wave = models.ForeignKey("Wave", on_delete=models.CASCADE)
#     additional_field = models.CharField(max_length=32)


# class Wave(models.Model):
#     """
#     Custom wave model.
#     """

#     id = models.UUIDField(
#         primary_key=True, default=uuid.uuid4, editable=False, blank=False
#     )
#     start_date = models.DateTimeField(blank=False)
#     end_date = models.DateTimeField(blank=False)
#     created_at = models.DateTimeField(auto_now_add=True, blank=False)
#     client_id = models.CharField(max_length=32, blank=False)
#     wave_number = models.IntegerField(blank=False)
#     wave_name = models.CharField(max_length=32, blank=False)
#     wave_type = models.CharField(max_length=32, blank=False)
#     wave_status = models.CharField(max_length=32, blank=False)
#     participants = models.ManyToManyField(Participant, through="WaveParticipant")

#     def __str__(self) -> str:
#         """
#         Returns the string representation of the wave.

#         Returns:
#             str: A formatted string with wave information.
#         """

#         return f"{self.client_id} - {self.wave_number} - {self.start_date} to {self.end_date}"
