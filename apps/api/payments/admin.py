from __future__ import annotations

from django.contrib import admin

from .models import LedgerEntry, Payout, Purchase, Tip, Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "aura_balance", "created_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("user", "aura_balance", "created_at")


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("wallet", "kind", "amount", "balance_after", "created_at")
    list_filter = ("kind",)
    readonly_fields = ("wallet", "amount", "kind", "reference", "balance_after", "created_at")


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "credits",
        "fiat_amount",
        "currency",
        "provider",
        "status",
        "created_at",
    )
    list_filter = ("status", "provider")
    search_fields = ("user__username", "provider_ref")


@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    list_display = (
        "from_user",
        "to_channel",
        "aura_amount",
        "creator_share",
        "platform_fee",
        "created_at",
    )
    search_fields = ("from_user__username", "to_channel__slug")


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ("user", "aura_amount", "fiat_amount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username",)
