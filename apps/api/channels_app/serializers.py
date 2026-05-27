"""Serializers : la clé RTMPS n'est exposée que sur l'endpoint owner /me."""

from __future__ import annotations

from rest_framework import serializers

from catalog.models import Game
from catalog.serializers import GameSerializer

from .models import Channel, StreamSession

# Réseaux sociaux autorisés sur le profil chaîne.
ALLOWED_SOCIAL_KEYS = frozenset({"twitter", "youtube", "instagram", "tiktok", "discord", "website"})


def _clean_social_links(value):
    if not isinstance(value, dict):
        raise serializers.ValidationError("Format attendu : objet {réseau: lien}.")
    cleaned = {}
    for key, link in value.items():
        if key not in ALLOWED_SOCIAL_KEYS:
            raise serializers.ValidationError(f"Réseau non supporté : {key}.")
        if link in (None, ""):
            continue
        if not isinstance(link, str) or len(link) > 200:
            raise serializers.ValidationError(f"Lien invalide pour {key}.")
        cleaned[key] = link
    return cleaned


class StreamSessionSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.IntegerField(read_only=True)
    category = serializers.SlugRelatedField(
        source="category_snapshot", slug_field="name", read_only=True
    )

    class Meta:
        model = StreamSession
        fields = (
            "started_at",
            "ended_at",
            "duration_seconds",
            "peak_viewers",
            "title_snapshot",
            "category",
        )
        read_only_fields = fields


class StreamerSerializer(serializers.Serializer):
    """Sous-payload streamer côté public."""

    username = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    avatar_url = serializers.URLField(read_only=True)
    bio = serializers.CharField(read_only=True)


class PublicChannelSerializer(serializers.ModelSerializer):
    streamer = StreamerSerializer(source="user", read_only=True)
    category = GameSerializer(read_only=True)

    class Meta:
        model = Channel
        fields = (
            "slug",
            "title",
            "thumbnail_url",
            "banner_url",
            "social_links",
            "hls_playback_url",
            "is_live",
            "last_live_started_at",
            "streamer",
            "category",
        )
        read_only_fields = fields


class MyChannelSerializer(serializers.ModelSerializer):
    """Vue propriétaire : inclut rtmps_url et rtmps_key. JAMAIS exposer ailleurs."""

    is_provisioned = serializers.BooleanField(read_only=True)
    category = GameSerializer(read_only=True)
    category_slug = serializers.SlugRelatedField(
        source="category",
        slug_field="slug",
        queryset=Game.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    social_links = serializers.JSONField(required=False)

    def validate_social_links(self, value):
        return _clean_social_links(value)

    class Meta:
        model = Channel
        fields = (
            "slug",
            "title",
            "thumbnail_url",
            "banner_url",
            "social_links",
            "rtmps_url",
            "rtmps_key",
            "hls_playback_url",
            "is_live",
            "is_provisioned",
            "last_live_started_at",
            "category",
            "category_slug",
        )
        read_only_fields = (
            "slug",
            "rtmps_url",
            "rtmps_key",
            "hls_playback_url",
            "is_live",
            "is_provisioned",
            "last_live_started_at",
        )
