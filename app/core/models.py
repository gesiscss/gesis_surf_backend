"""
This file is used to create models for the core app.
"""

import uuid
from typing import Any

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


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


class Privacy(models.Model):
    """
    Custom privacy model.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, blank=False
    )
    # Store the user who created the privacy
    # Relationship one-to-one with the user model
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="privacy",
    )
    privacy_mode = models.BooleanField(default=False)
    privacy_start_time = models.DateTimeField(blank=True, default=timezone.now)
    privacy_end_time = models.DateTimeField(blank=True, default=timezone.now)
    history = HistoricalRecords()

    def __str__(self) -> str:
        """
        Returns the string representation of the privacy.

        Returns:
            str: A formatted string with privacy information.
        """
        # Return information about the privacy at admin panel
        return f"{self.privacy_mode} to {self.privacy_start_time}"


class Extension(models.Model):
    """
    Custom extension model.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, blank=False
    )
    # Store the user who created the extension
    # Relationship one-to-one with the user model
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="extension",
    )
    extension_version = models.CharField(max_length=32, blank=True)
    extension_installed_at = models.DateTimeField(blank=True, null=True)
    extension_updated_at = models.DateTimeField(blank=True, null=True)
    extension_browser = models.CharField(max_length=128, blank=True)
    history = HistoricalRecords()

    def __str__(self) -> str:
        """
        Returns the string representation of the extension.

        Returns:
            str: A formatted string with extension information.
        """
        # Return information about the extension at admin panel
        return f"{self.extension_version} to {self.extension_installed_at}"


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
    wave_status = models.CharField(max_length=32, blank=False)
    wave_type = models.CharField(max_length=32, blank=False)
    wave_number = models.CharField(max_length=32, blank=False)
    client_id = models.CharField(max_length=32, blank=False)
    # Create a relationship with the user model
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)

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
    # Store the user who created the window
    # Relationship with the user model
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        # related_name="windows",
    )
    start_time = models.DateTimeField(blank=True)
    closing_time = models.DateTimeField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=False)
    window_num = models.CharField(max_length=32, blank=False)

    def __str__(self) -> str:
        """
        Returns the string representation of the window.

        Returns:
            str: A formatted string with window information.
        """
        # Return information about the window at admin panel
        return f"{self.start_time} to {self.closing_time}"


class Tab(models.Model):
    """
    Custom tab model.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, blank=False
    )
    # Store the user who created the tab
    # Relationship with the user model
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tabs",
    )
    start_time = models.DateTimeField(blank=True)
    closing_time = models.DateTimeField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=False)
    tab_num = models.CharField(max_length=32, blank=False)
    window_num = models.CharField(max_length=32, blank=False)
    # Create a relationship with the window model
    # window = models.ForeignKey(
    #     Window,
    #     on_delete=models.CASCADE,
    #     related_name="tabs",
    # )
    domains = models.ManyToManyField("Domain")

    def __str__(self) -> str:
        """
        Returns the string representation of the tab.

        Returns:
            str: A formatted string with tab information.
        """
        # Return information about the tab at admin panel
        return f"{self.start_time} to {self.closing_time}"


class Domain(models.Model):
    """
    Custom domain model.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, blank=False
    )
    # Store the user who created the domain
    # Relationship with the user model
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="domains",
    )
    domain_title = models.CharField(blank=False)
    snapshot_html = models.TextField(blank=True)
    domain_status = models.CharField(blank=False)
    domain_fav_icon = models.CharField(blank=False)
    start_time = models.DateTimeField(blank=True, default=timezone.now)
    closing_time = models.DateTimeField(blank=True, default=timezone.now)
    domain_url = models.CharField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=False)
    category_number = models.CharField(max_length=32, blank=False, default="0")
    criteria_classification = models.CharField(
        max_length=32, blank=False, default="full_allow"
    )
    category_label = models.CharField(max_length=32, blank=False, default="0")

    def __str__(self) -> str:
        """
        Returns the string representation of the domain.

        Returns:
            str: A formatted string with domain information.
        """
        # Return information about the domain at admin panel
        return f"{self.domain_title} to {self.domain_url}"


class Click(models.Model):
    """
    Custom click model.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, blank=False
    )
    # Store the user who created the click
    # Relationship with the user model
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clicks",
    )
    click_time = models.DateTimeField(blank=True)
    click_type = models.CharField(max_length=32, blank=False)
    click_target_element = models.CharField(max_length=100, blank=False, default="0")
    click_target_tag = models.CharField(max_length=200, blank=False, default="0")
    click_target_id = models.CharField(max_length=200, blank=False, default="0")
    click_target_class = models.CharField(max_length=200, blank=False, default="0")
    click_page_x = models.FloatField(blank=False, default=0)
    click_page_y = models.FloatField(blank=False, default=0)
    click_referrer = models.CharField(max_length=200, default="0")
    created_at = models.DateTimeField(auto_now_add=True, blank=False)
    domain = models.ForeignKey(
        Domain,
        on_delete=models.CASCADE,
        related_name="clicks",
    )

    def __str__(self) -> str:
        """
        Returns the string representation of the click.

        Returns:
            str: A formatted string with click information.
        """
        # Return information about the click at admin panel
        return f"{self.click_time} to {self.click_type}"


class Scroll(models.Model):
    """
    Create a scroll model.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, blank=False
    )
    # Store the user who created the scroll
    # Relationship with the user model
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scrolls",
    )
    scroll_time = models.DateTimeField(blank=True)
    scroll_x = models.FloatField(blank=False)
    scroll_y = models.FloatField(blank=False)
    page_x_offset = models.FloatField(blank=False)
    page_y_offset = models.FloatField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=False)
    domain = models.ForeignKey(
        Domain,
        on_delete=models.CASCADE,
        related_name="scrolls",
    )


class Host(models.Model):
    """
    Create the url model.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, blank=False
    )
    hostname = models.CharField(max_length=32, blank=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=False)
    categories = models.ManyToManyField("Category", related_name="hosts")
    version = models.CharField(max_length=32, blank=False, default="0")


class Category(models.Model):
    """
    Create the category model.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, blank=False
    )
    category_number = models.CharField(max_length=32, blank=False, default="0")
    category_score = models.FloatField(blank=False)
    category_parent = models.CharField(max_length=32, blank=False)
    category_label = models.CharField(max_length=32, blank=False)
    category_confidence = models.FloatField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=False)
    criteria = models.ForeignKey(
        "Criteria",
        on_delete=models.CASCADE,
        related_name="categories",
        null=True,
    )


class Criteria(models.Model):
    """
    Create the criteria model.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, blank=False
    )
    criteria_classification = models.CharField(max_length=32, blank=False)
    criteria_window = models.BooleanField(blank=False)
    criteria_tab = models.BooleanField(blank=False)
    criteria_domain = models.BooleanField(blank=False)
    criteria_click = models.BooleanField(blank=False)
    criteria_scroll = models.BooleanField(blank=False)
    snapshot_html = models.BooleanField(blank=False, default=False)
