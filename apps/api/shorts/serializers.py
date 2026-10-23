from __future__ import annotations

from rest_framework import serializers

from .models import Short


class ShortSerializer(serializers.ModelSerializer):
    channel = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()

    class Meta:
        model = Short
        fields = (
            "id",
            "title",
            "thumbnail_url",
            "playback_url",
            "duration_s",
            "view_count",
            "like_count",
            "published_at",
            "channel",
            "liked",
        )
        read_only_fields = fields

    def get_channel(self, obj):
        c, u = obj.channel, obj.channel.user
        return {
            "slug": c.slug,
            "is_live": c.is_live,
            "streamer": {
                "username": u.username,
                "display_name": u.display_name,
                "avatar_url": u.avatar_url,
            },
        }

    def get_liked(self, obj) -> bool:
        liked_ids = self.context.get("liked_ids")
        return bool(liked_ids and obj.pk in liked_ids)


class MyShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Short
        fields = (
            "id",
            "title",
            "status",
            "thumbnail_url",
            "playback_url",
            "duration_s",
            "view_count",
            "like_count",
            "is_published",
            "created_at",
            "published_at",
        )
        read_only_fields = fields


class ShortCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=120)
