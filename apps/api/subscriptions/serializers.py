from __future__ import annotations

from rest_framework import serializers

from .models import SubTier


class SubTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTier
        fields = ("name", "price_aura", "perks", "is_active")


class TierWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=60, required=False, default="Abonnement")
    price_aura = serializers.IntegerField(min_value=1, max_value=1_000_000)
    perks = serializers.ListField(
        child=serializers.CharField(max_length=120), required=False, default=list
    )
    is_active = serializers.BooleanField(required=False, default=True)
