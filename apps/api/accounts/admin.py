from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import GuideProgress, TwoFactor, User, UserSession


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("-date_joined",)
    date_hierarchy = "date_joined"
    list_per_page = 50
    list_editable = ("role", "is_active")
    list_display = (
        "email",
        "username",
        "role",
        "is_staff",
        "is_active",
        "email_verified_at",
        "date_joined",
    )
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "username", "display_name")
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Profil", {"fields": ("display_name", "avatar_url", "bio")}),
        ("Rôle", {"fields": ("role",)}),
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


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "device", "ip", "revoked", "created_at", "last_seen_at")
    list_filter = ("revoked",)
    search_fields = ("user__username", "ip")
    readonly_fields = ("user", "jti", "device", "ip", "created_at", "last_seen_at")


@admin.register(TwoFactor)
class TwoFactorAdmin(admin.ModelAdmin):
    list_display = ("user", "enabled", "confirmed_at", "updated_at")
    list_filter = ("enabled",)
    search_fields = ("user__username",)
    readonly_fields = ("user", "secret", "recovery_codes", "created_at", "updated_at")


@admin.register(GuideProgress)
class GuideProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "key", "completed_at")
    search_fields = ("user__username", "key")
    readonly_fields = ("user", "key", "completed_at")
