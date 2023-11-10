"""
This file is used to create models for the core app.
"""

from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


class UserManager(BaseUserManager) -> None:
    """
    User manager class.
    """

    def create_user(self, email: str, password: str = None, **extra_fields) -> None:
        """
        Creates and saves a new user.
        """
        if not email:
            raise ValueError("Users must have an email address.")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str) -> None:
        """
        Creates and saves a new superuser.
        """
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)