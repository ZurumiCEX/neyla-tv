from __future__ import annotations

from rest_framework import serializers

from .models import FeeRule, LedgerEntry, Payout, PayoutDestination, Purchase, Wallet


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = (
            "amount",
            "kind",
            "reference",
            "balance_after",
            "currency",
            "related_type",
            "related_id",
            "metadata",
            "created_at",
        )
        read_only_fields = fields


class FeeRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeRule
        fields = ("id", "product", "mode", "value", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        mode = attrs.get("mode", getattr(self.instance, "mode", FeeRule.Mode.PERCENTAGE))
        value = attrs.get("value", getattr(self.instance, "value", None))
        if value is not None and value < 0:
            raise serializers.ValidationError({"value": "La commission ne peut pas être négative."})
        if mode == FeeRule.Mode.PERCENTAGE and value is not None and value > 100:
            raise serializers.ValidationError({"value": "Un pourcentage ne peut pas dépasser 100."})
        return attrs


class WalletSerializer(serializers.ModelSerializer):
    recent = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    unit_price_xof = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ("aura_balance", "balance", "unit_price_xof", "payout_hold", "recent")
        read_only_fields = fields

    def get_recent(self, obj):
        return LedgerEntrySerializer(obj.entries.all()[:20], many=True).data

    def get_unit_price_xof(self, obj):  # noqa: ARG002
        from . import services

        return str(services.aura_unit_price())

    def get_balance(self, obj):
        """Équivalents fiat (XOF/EUR/USD) du solde Aura."""
        from . import conversion, services

        return conversion.equivalents(services.aura_unit_price() * obj.aura_balance)


class PurchaseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = (
            "id",
            "credits",
            "fiat_amount",
            "currency",
            "provider",
            "status",
            "created_at",
        )
        read_only_fields = fields


class PurchaseSerializer(serializers.Serializer):
    credits = serializers.IntegerField(min_value=1, max_value=1_000_000)
    method = serializers.ChoiceField(
        choices=["card", "orange_money", "wave"], required=False, default="card"
    )


class TipSerializer(serializers.Serializer):
    channel_slug = serializers.CharField()
    aura_amount = serializers.IntegerField(min_value=1, max_value=1_000_000)
    message = serializers.CharField(required=False, allow_blank=True, default="", max_length=200)


class PayoutHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = (
            "id",
            "aura_amount",
            "fee_aura",
            "fiat_amount",
            "currency",
            "destination_provider",
            "destination_phone",
            "status",
            "created_at",
            "resolved_at",
        )
        read_only_fields = fields


class WithdrawalQuoteSerializer(serializers.Serializer):
    aura_amount = serializers.IntegerField(min_value=1, max_value=1_000_000)


class WithdrawalStartSerializer(WithdrawalQuoteSerializer):
    destination_provider = serializers.ChoiceField(choices=PayoutDestination.choices)
    destination_phone = serializers.CharField(max_length=20)


class WithdrawalConfirmSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)
