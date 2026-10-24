"""Serializers : validation entrée + sérialisation sortie. Pas de logique métier."""

from __future__ import annotations

import datetime

from rest_framework import serializers

from .models import USERNAME_REGEX, User, UserSession

MIN_AGE_YEARS = 18
PASSWORD_MIN_LENGTH = 8


def age_on(birth: datetime.date, today: datetime.date) -> int:
    """Âge révolu à la date `today` (un 29 février compte au 28 les années non bissextiles)."""
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.RegexField(
        USERNAME_REGEX,
        error_messages={
            "invalid": "3 à 30 caractères : lettres minuscules, chiffres ou « _ » uniquement."
        },
    )
    password = serializers.CharField(
        write_only=True, min_length=PASSWORD_MIN_LENGTH, max_length=128
    )
    password_confirm = serializers.CharField(write_only=True, max_length=128)
    date_of_birth = serializers.DateField(
        error_messages={
            "required": "Ta date de naissance est requise.",
            "invalid": "Date de naissance invalide (format AAAA-MM-JJ).",
        }
    )
    invite = serializers.CharField(required=False, allow_blank=True, default="", max_length=16)
    terms_accepted = serializers.BooleanField(write_only=True)
    # Honeypot : champ invisible côté UI ; rempli ⇒ bot.
    website = serializers.CharField(
        required=False, allow_blank=True, default="", write_only=True, max_length=200
    )
    # Token Cloudflare Turnstile (vérifié côté vue). Optionnel en mode FAKE.
    captcha_token = serializers.CharField(
        required=False, allow_blank=True, default="", write_only=True, max_length=2048
    )

    def validate_terms_accepted(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError(
                "Vous devez attester avoir 18 ans ou plus et accepter les conditions d'utilisation."
            )
        return value

    def validate_date_of_birth(self, value: datetime.date) -> datetime.date:
        today = datetime.date.today()
        if value > today or value.year < 1900:
            raise serializers.ValidationError("Date de naissance invalide.")
        if age_on(value, today) < MIN_AGE_YEARS:
            raise serializers.ValidationError(
                f"Neyla TV est réservée aux personnes de {MIN_AGE_YEARS} ans ou plus."
            )
        return value

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Les deux mots de passe ne correspondent pas."}
            )
        return attrs

    def validate_website(self, value: str) -> str:
        # Honeypot : aucun utilisateur réel ne remplit ce champ.
        if value:
            raise serializers.ValidationError("Spam détecté.")
        return value

    def validate_email(self, value: str) -> str:
        from safety.captcha import is_disposable

        if is_disposable(value):
            raise serializers.ValidationError("Ce domaine d'email n'est pas autorisé.")
        return value


class PublicUserSerializer(serializers.ModelSerializer):
    """Profil public visible par tout le monde."""

    class Meta:
        model = User
        fields = ("id", "username", "display_name", "avatar_url", "bio")
        read_only_fields = fields


class MeSerializer(serializers.ModelSerializer):
    """Profil privé de l'utilisateur courant (lecture + update partielle)."""

    is_email_verified = serializers.BooleanField(read_only=True)
    is_streamer = serializers.SerializerMethodField()
    two_factor_enabled = serializers.SerializerMethodField()
    strong_auth_required = serializers.SerializerMethodField()
    social_links = serializers.JSONField(required=False)

    def get_two_factor_enabled(self, obj) -> bool:
        tf = getattr(obj, "two_factor", None)
        return bool(tf and tf.enabled)

    def get_strong_auth_required(self, obj) -> bool:
        """Membre de l'équipe sans 2FA ni passkey alors que la console l'exige."""
        from django.conf import settings

        from .permissions import has_strong_auth

        staff = obj.role in ("admin", "moderator", "support") or obj.is_superuser
        return bool(
            staff and getattr(settings, "REQUIRE_STAFF_2FA", False) and not has_strong_auth(obj)
        )

    _ALLOWED_SOCIAL = frozenset({"twitter", "youtube", "instagram", "tiktok", "discord", "website"})

    def get_is_streamer(self, obj) -> bool:
        from channels_app.utils import is_streamer

        return is_streamer(obj)

    def validate_social_links(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Format attendu : objet {réseau: lien}.")
        cleaned = {}
        for key, link in value.items():
            if key not in self._ALLOWED_SOCIAL:
                raise serializers.ValidationError(f"Réseau non supporté : {key}.")
            if link in (None, ""):
                continue
            if not isinstance(link, str) or len(link) > 200:
                raise serializers.ValidationError(f"Lien invalide pour {key}.")
            cleaned[key] = link
        return cleaned

    def validate_country(self, value):
        value = (value or "").strip().upper()
        if value and len(value) != 2:
            raise serializers.ValidationError("Code pays ISO à 2 lettres attendu.")
        return value

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "display_name",
            "avatar_url",
            "bio",
            "country",
            "social_links",
            "is_email_verified",
            "is_staff",
            "is_superuser",
            "is_streamer",
            "two_factor_enabled",
            "strong_auth_required",
            "role",
            "date_joined",
        )
        read_only_fields = (
            "id",
            "email",
            "username",
            "is_email_verified",
            "is_staff",
            "is_superuser",
            "is_streamer",
            "two_factor_enabled",
            "strong_auth_required",
            "role",
            "date_joined",
        )


class AdminUserSerializer(serializers.ModelSerializer):
    """Vue admin d'un utilisateur (liste + édition du rôle)."""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "display_name",
            "role",
            "is_active",
            "date_joined",
            "last_active_at",
        )
        read_only_fields = ("id", "username", "email", "display_name", "date_joined")


class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = ("id", "device", "ip", "created_at", "last_seen_at")
        read_only_fields = fields


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, max_length=128)
