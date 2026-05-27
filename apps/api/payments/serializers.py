from __future__ import annotations

from rest_framework import serializers

from .models import LedgerEntry, Wallet


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = ("amount", "kind", "reference", "balance_after", "created_at")
        read_only_fields = fields


class WalletSerializer(serializers.ModelSerializer):
    recent = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ("aura_balance", "recent")
        read_only_fields = fields

    def get_recent(self, obj):
        return LedgerEntrySerializer(obj.entries.all()[:20], many=True).data


class PurchaseSerializer(serializers.Serializer):
    credits = serializers.IntegerField(min_value=1, max_value=1_000_000)


class TipSerializer(serializers.Serializer):
    channel_slug = serializers.CharField()
    aura_amount = serializers.IntegerField(min_value=1, max_value=1_000_000)
    message = serializers.CharField(required=False, allow_blank=True, default="", max_length=200)


class PayoutSerializer(serializers.Serializer):
    aura_amount = serializers.IntegerField(min_value=1, max_value=1_000_000)
