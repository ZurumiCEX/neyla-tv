from __future__ import annotations

from rest_framework import serializers

from .models import ContentFlag, RiskEvent


class RiskEventSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = RiskEvent
        fields = (
            "id",
            "username",
            "kind",
            "severity",
            "detail",
            "resolved",
            "created_at",
        )
        read_only_fields = fields


class ContentFlagSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    channel_slug = serializers.SerializerMethodField()

    class Meta:
        model = ContentFlag
        fields = (
            "id",
            "username",
            "channel_slug",
            "source",
            "category",
            "confidence",
            "text",
            "url",
            "scores",
            "status",
            "created_at",
        )
        read_only_fields = fields

    def get_username(self, obj) -> str:
        return obj.user.username if obj.user_id else ""

    def get_channel_slug(self, obj) -> str:
        return obj.channel.slug if obj.channel_id else ""
