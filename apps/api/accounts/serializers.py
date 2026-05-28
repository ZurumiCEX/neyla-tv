"""Serializers : validation entrée + sérialisation sortie. Pas de logique métier."""

from __future__ import annotations

from rest_framework import serializers

from .models import USERNAME_REGEX, User


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.RegexField(USERNAME_REGEX)
    password = serializers.CharField(write_only=True, min_length=10, max_length=128)
    invite = serializers.CharField(required=False, allow_blank=True, default="", max_length=16)


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
    social_links = serializers.JSONField(required=False)

    _ALLOWED_SOCIAL = frozenset({"twitter", "youtube", "instagram", "tiktok", "discord", "website"})

    def get_is_streamer(self, obj) -> bool:
        try:
            return obj.channel.is_provisioned
        except Exception:
            return False

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
            "is_streamer",
            "role",
            "date_joined",
        )
        read_only_fields = (
            "id",
            "email",
            "username",
            "is_email_verified",
            "is_staff",
            "is_streamer",
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


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(min_length=10, max_length=128)
