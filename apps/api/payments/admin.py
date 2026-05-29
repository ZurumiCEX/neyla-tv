from __future__ import annotations

from django.contrib import admin, messages

from .models import FeeRule, LedgerEntry, Payout, PayoutOtp, Purchase, Tip, Wallet


class LedgerEntryInline(admin.TabularInline):
    """Mouvements Aura du portefeuille, en lecture seule."""

    model = LedgerEntry
    extra = 0
    can_delete = False
    ordering = ("-created_at",)
    fields = ("created_at", "kind", "amount", "balance_after", "reference")
    readonly_fields = fields
    verbose_name_plural = "Mouvements"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(FeeRule)
class FeeRuleAdmin(admin.ModelAdmin):
    list_display = ("product", "mode", "value", "is_active", "updated_at")
    list_filter = ("product", "mode", "is_active")
    list_editable = ("value", "is_active")
    ordering = ("product", "-updated_at")


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "aura_balance", "created_at")
    search_fields = ("user__username", "user__email")
    list_select_related = ("user",)
    ordering = ("-aura_balance",)
    list_per_page = 50
    inlines = (LedgerEntryInline,)
    readonly_fields = ("user", "aura_balance", "created_at")


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("wallet", "kind", "amount", "balance_after", "created_at")
    list_filter = ("kind", "created_at")
    search_fields = ("wallet__user__username", "reference")
    date_hierarchy = "created_at"
    list_select_related = ("wallet__user",)
    list_per_page = 50
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
    list_filter = ("status", "provider", "currency", "created_at")
    search_fields = ("user__username", "provider_ref")
    date_hierarchy = "created_at"
    list_select_related = ("user",)
    list_per_page = 50
    ordering = ("-created_at",)


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
    list_filter = ("created_at",)
    date_hierarchy = "created_at"
    list_select_related = ("from_user", "to_channel")
    list_per_page = 50


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ("user", "aura_amount", "fiat_amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username",)
    date_hierarchy = "created_at"
    list_select_related = ("user",)
    list_per_page = 50
    actions = ("mark_paid", "mark_failed")

    @admin.action(description="Marquer comme payé")
    def mark_paid(self, request, queryset):
        self._resolve(request, queryset, "paid")

    @admin.action(description="Rejeter et rembourser")
    def mark_failed(self, request, queryset):
        self._resolve(request, queryset, "fail")

    def _resolve(self, request, queryset, action: str):
        from . import services

        done = 0
        for payout in queryset:
            try:
                services.resolve_payout(request.user, payout, action)
                done += 1
            except services.PaymentError as exc:
                self.message_user(request, f"#{payout.id}: {exc}", level=messages.WARNING)
        self.message_user(request, f"{done} retrait(s) traité(s).", level=messages.SUCCESS)


@admin.register(PayoutOtp)
class PayoutOtpAdmin(admin.ModelAdmin):
    list_display = ("user", "aura_amount", "consumed", "created_at", "expires_at")
    list_filter = ("consumed", "created_at")
    search_fields = ("user__username",)
    date_hierarchy = "created_at"
    readonly_fields = ("user", "aura_amount", "code_hash", "created_at", "expires_at")
