"""Serializers : la clé RTMPS n'est exposée que sur l'endpoint owner /me."""

from __future__ import annotations

from rest_framework import serializers

from catalog.models import Game
from catalog.serializers import GameSerializer

from .models import Channel


class StreamerSerializer(serializers.Serializer):
    """Sous-payload streamer côté public."""

    username = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    avatar_url = serializers.URLField(read_only=True)


class PublicChannelSerializer(serializers.ModelSerializer):
    streamer = StreamerSerializer(source="user", read_only=True)
    category = GameSerializer(read_only=True)

    class Meta:
        model = Channel
        fields = (
            "slug",
            "title",
            "thumbnail_url",
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

    class Meta:
        model = Channel
        fields = (
            "slug",
            "title",
            "thumbnail_url",
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
