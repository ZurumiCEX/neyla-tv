"""User custom : email + username comme identité publique. Profil enrichi en Phase 1."""

from __future__ import annotations

from django.conf import settings
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
    country = models.CharField(max_length=2, blank=True)  # code ISO-3166-1 alpha-2
    social_links = models.JSONField(default=dict, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)

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


class UserSession(models.Model):
    """Session d'appareil adossée au refresh token (jti courant).

    Permet à l'utilisateur de voir ses appareils connectés et de les révoquer.
    Le jti suit la rotation des refresh tokens.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions"
    )
    jti = models.CharField(max_length=64, unique=True, db_index=True)
    device = models.CharField(max_length=300, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    revoked = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_seen_at"]

    def __str__(self) -> str:
        return f"session:{self.user_id}:{self.jti[:8]}"


class TwoFactor(models.Model):
    """Configuration TOTP (2FA) d'un utilisateur + codes de secours hachés."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="two_factor"
    )
    secret = models.CharField(max_length=64)
    enabled = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    # Codes de secours : liste de SHA-256 (hex). Consommés à l'usage.
    recovery_codes = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"2fa:{self.user_id}:{'on' if self.enabled else 'off'}"


class GuideProgress(models.Model):
    """Suivi des acquis : étapes de tutoriels validées par un utilisateur.

    `key` = "<guide_slug>:<step_id>". Le contenu des guides est géré en base
    (modèles `Guide`/`GuideStep`), la persistance ne stocke que les clés validées.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guide_progress"
    )
    key = models.CharField(max_length=120)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "key"], name="uniq_guide_progress")]
        indexes = [models.Index(fields=["user"])]

    def __str__(self) -> str:
        return f"guide:{self.user_id}:{self.key}"


class Guide(models.Model):
    """Guide / tutoriel géré en back-office (contenu localisé FR/EN/PT)."""

    class Icon(models.TextChoices):
        ROCKET = "rocket", "Fusée"
        BROADCAST = "broadcast", "Diffusion"
        COINS = "coins", "Pièces"
        SHIELD = "shield", "Bouclier"

    slug = models.SlugField(max_length=60, unique=True)
    icon = models.CharField(max_length=20, choices=Icon.choices, default=Icon.ROCKET)
    order = models.PositiveIntegerField(default=0, db_index=True)
    is_published = models.BooleanField(default=True, db_index=True)

    title_fr = models.CharField(max_length=120)
    title_en = models.CharField(max_length=120, blank=True)
    title_pt = models.CharField(max_length=120, blank=True)
    desc_fr = models.CharField(max_length=300, blank=True)
    desc_en = models.CharField(max_length=300, blank=True)
    desc_pt = models.CharField(max_length=300, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.slug} ({self.title_fr})"

    def title(self, locale: str) -> str:
        return getattr(self, f"title_{locale}", "") or self.title_fr

    def desc(self, locale: str) -> str:
        return getattr(self, f"desc_{locale}", "") or self.desc_fr


class GuideStep(models.Model):
    """Étape d'un guide. `step_id` est stable (clé de progression)."""

    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name="steps")
    step_id = models.SlugField(max_length=60)
    order = models.PositiveIntegerField(default=0, db_index=True)

    title_fr = models.CharField(max_length=160)
    title_en = models.CharField(max_length=160, blank=True)
    title_pt = models.CharField(max_length=160, blank=True)
    body_fr = models.TextField(blank=True)
    body_en = models.TextField(blank=True)
    body_pt = models.TextField(blank=True)

    class Meta:
        ordering = ["order", "id"]
        constraints = [models.UniqueConstraint(fields=["guide", "step_id"], name="uniq_guide_step")]

    def __str__(self) -> str:
        return f"{self.guide.slug}:{self.step_id}"

    def title(self, locale: str) -> str:
        return getattr(self, f"title_{locale}", "") or self.title_fr

    def body(self, locale: str) -> str:
        return getattr(self, f"body_{locale}", "") or self.body_fr
