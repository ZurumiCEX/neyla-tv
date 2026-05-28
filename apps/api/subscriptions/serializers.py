from __future__ import annotations

from rest_framework import serializers

from .models import Subscription, SubTier


class SubTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTier
        fields = ("name", "price_aura", "perks", "is_active")


class MySubscriptionSerializer(serializers.ModelSerializer):
    channel = serializers.SerializerMethodField()
    tier_name = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ("channel", "tier_name", "status", "current_period_end")
        read_only_fields = fields

    def get_channel(self, obj):
        c = obj.channel
        u = c.user
        return {
            "slug": c.slug,
            "title": c.title,
            "thumbnail_url": c.thumbnail_url,
            "is_live": c.is_live,
            "streamer": {
                "username": u.username,
                "display_name": u.display_name,
                "avatar_url": u.avatar_url,
            },
            "category": (
                {"slug": c.category.slug, "name": c.category.name} if c.category else None
            ),
        }

    def get_tier_name(self, obj):
        return obj.tier.name if obj.tier else None


class TierWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=60, required=False, default="Abonnement")
    price_aura = serializers.IntegerField(min_value=1, max_value=1_000_000)
    perks = serializers.ListField(
        child=serializers.CharField(max_length=120), required=False, default=list
    )
    is_active = serializers.BooleanField(required=False, default=True)
