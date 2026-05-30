from __future__ import annotations

from rest_framework import serializers

from .models import Subscription, SubTier


class SubTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTier
        fields = ("name", "price_aura", "perks", "is_active")


def _channel_payload(c):
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
        "category": ({"slug": c.category.slug, "name": c.category.name} if c.category else None),
    }


class MySubscriptionSerializer(serializers.ModelSerializer):
    channel = serializers.SerializerMethodField()
    tier_name = serializers.SerializerMethodField()
    gifted_by = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ("channel", "tier_name", "status", "current_period_end", "gifted_by")
        read_only_fields = fields

    def get_channel(self, obj):
        return _channel_payload(obj.channel)

    def get_tier_name(self, obj):
        return obj.tier.name if obj.tier else None

    def get_gifted_by(self, obj):
        g = obj.gifted_by
        return {"username": g.username, "display_name": g.display_name} if g else None


class GiftedSubscriptionSerializer(serializers.ModelSerializer):
    """Abonnement que j'ai offert : montre le destinataire + la chaîne."""

    channel = serializers.SerializerMethodField()
    tier_name = serializers.SerializerMethodField()
    recipient = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ("channel", "tier_name", "recipient", "status", "current_period_end", "created_at")
        read_only_fields = fields

    def get_channel(self, obj):
        return _channel_payload(obj.channel)

    def get_tier_name(self, obj):
        return obj.tier.name if obj.tier else None

    def get_recipient(self, obj):
        r = obj.subscriber
        return {
            "username": r.username,
            "display_name": r.display_name,
            "avatar_url": r.avatar_url,
        }


class TierWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=60, required=False, default="Abonnement")
    price_aura = serializers.IntegerField(min_value=1, max_value=1_000_000)
    perks = serializers.ListField(
        child=serializers.CharField(max_length=120), required=False, default=list
    )
    is_active = serializers.BooleanField(required=False, default=True)
