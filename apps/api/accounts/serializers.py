"""Serializers : validation entrée + sérialisation sortie. Pas de logique métier."""

from __future__ import annotations

from rest_framework import serializers

from .models import USERNAME_REGEX, User


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.RegexField(USERNAME_REGEX)
    password = serializers.CharField(write_only=True, min_length=10, max_length=128)


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

    def get_is_streamer(self, obj) -> bool:
        try:
            return obj.channel.is_provisioned
        except Exception:
            return False

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "display_name",
            "avatar_url",
            "bio",
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


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(min_length=10, max_length=128)
