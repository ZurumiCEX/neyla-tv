"""User custom : email + username comme identité publique. Profil enrichi en Phase 1."""

from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from .managers import UserManager

USERNAME_REGEX = r"^[a-z0-9_]{3,30}$"

RESERVED_USERNAMES = frozenset(
    {
        "admin",
        "api",
        "auth",
        "c",
        "live",
        "login",
        "register",
        "settings",
        "neyla",
        "support",
        "root",
        "me",
    }
)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        USER = "user", "Utilisateur"
        SUPPORT = "support", "Support"
        MODERATOR = "moderator", "Modérateur"
        ADMIN = "admin", "Administrateur"

    email = models.EmailField(unique=True)
    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[RegexValidator(USERNAME_REGEX, "Slug invalide.")],
    )
    display_name = models.CharField(max_length=60, blank=True)
    avatar_url = models.URLField(blank=True)
    bio = models.TextField(max_length=500, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    role = models.CharField(max_length=12, choices=Role.choices, default=Role.USER, db_index=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_active_at = models.DateTimeField(null=True, blank=True, db_index=True)
    invited_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_users",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = ["username"]

    objects = UserManager()

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.email

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def is_staff_role(self) -> bool:
        """True pour support/modérateur/admin (rôles internes)."""
        return self.role in (self.Role.SUPPORT, self.Role.MODERATOR, self.Role.ADMIN)
