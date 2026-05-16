from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = (
        "email",
        "username",
        "is_staff",
        "is_active",
        "email_verified_at",
        "date_joined",
    )
    list_filter = ("is_staff", "is_active")
    search_fields = ("email", "username", "display_name")
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Profil", {"fields": ("display_name", "avatar_url", "bio")}),
        ("Vérification", {"fields": ("email_verified_at",)}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {"classes": ("wide",), "fields": ("email", "username", "password1", "password2")},
        ),
    )
