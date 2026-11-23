"""
Django admin customization.
"""

from core import models
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _


class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users"""

    ordering = ["id"]
    list_display = [
        "user_id",
        "is_active",
        "is_staff",
        "is_superuser",
        "last_login",
        "created_at",
    ]
    fieldsets = (
        (None, {"fields": ("user_id", "password")}),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser")},
        ),
        (_("Important Dates"), {"fields": ("last_login",)}),
    )
    readonly_fields = ["last_login"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "user_id",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Wave)
admin.site.register(models.Window)
admin.site.register(models.Tab)
admin.site.register(models.Domain)
admin.site.register(models.Click)
admin.site.register(models.Scroll)
admin.site.register(models.Host)
admin.site.register(models.Category)
admin.site.register(models.Criteria)
admin.site.register(models.Privacy)
admin.site.register(models.Extension)
admin.site.register(models.SelectorConfig)


class MobilePolicyReleaseAdmin(admin.ModelAdmin):
    """
    Define the admin pages for the published mobile policy releases.

    Releases are immutable snapshots: they are inspected here, created and
    activated by the publish command, and never deleted.
    """

    readonly_fields = [
        "version",
        "policy_hash",
        "payload",
        "is_active",
        "created_at",
        "created_by",
    ]

    def has_add_permission(  # pylint: disable=unused-argument
        self, request: HttpRequest
    ) -> bool:
        """Releases are created by the publish command only."""
        return False

    def has_delete_permission(  # pylint: disable=unused-argument
        self, request: HttpRequest, obj: models.MobilePolicyRelease | None = None
    ) -> bool:
        """Old releases are kept for replay and rollback."""
        return False


admin.site.register(models.MobileApp)
admin.site.register(models.MobilePolicyRelease, MobilePolicyReleaseAdmin)
admin.site.register(models.MobileClient)
