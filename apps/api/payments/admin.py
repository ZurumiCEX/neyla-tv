from __future__ import annotations

from django import forms
from django.contrib import admin, messages
from django.db.models import Sum
from django.template.response import TemplateResponse

from config.admin_widgets import stat_grid

from .models import (
    FeeRule,
    LedgerEntry,
    Payout,
    PayoutOtp,
    PlatformRevenue,
    Purchase,
    Tip,
    Wallet,
)


class AuraAdjustmentForm(forms.Form):
    """Formulaire intermédiaire de l'action d'ajustement de solde Aura."""

    amount = forms.IntegerField(
        label="Montant Aura (négatif pour débiter)",
        help_text="Ex. 500 pour créditer, -200 pour débiter.",
    )
    reason = forms.CharField(
        label="Motif", widget=forms.Textarea(attrs={"rows": 3}), max_length=255
    )


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
    actions = ("adjust_aura",)
    readonly_fields = ("ledger_summary", "user", "aura_balance", "created_at")

    @admin.action(description="Ajuster le solde Aura…")
    def adjust_aura(self, request, queryset):
        from . import services

        if "apply" in request.POST:
            form = AuraAdjustmentForm(request.POST)
            if form.is_valid():
                amount = form.cleaned_data["amount"]
                reason = form.cleaned_data["reason"]
                done = 0
                for wallet in queryset:
                    try:
                        services.adjust_balance(request.user, wallet.user, amount, reason)
                        done += 1
                    except services.PaymentError as exc:
                        self.message_user(request, f"{wallet.user}: {exc}", level=messages.WARNING)
                self.message_user(
                    request, f"{done} portefeuille(s) ajusté(s).", level=messages.SUCCESS
                )
                return None
        else:
            form = AuraAdjustmentForm()
        context = {
            **self.admin_site.each_context(request),
            "title": "Ajuster le solde Aura",
            "wallets": queryset,
            "form": form,
            "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
            "selected": queryset.values_list("pk", flat=True),
            "opts": self.model._meta,
        }
        return TemplateResponse(request, "admin/payments/adjust_aura.html", context)

    @admin.display(description="Synthèse des mouvements")
    def ledger_summary(self, obj: Wallet):
        if obj is None or obj.pk is None:
            return "—"
        entries = obj.entries.all()
        credits = entries.filter(amount__gt=0).aggregate(s=Sum("amount"))["s"] or 0
        debits = entries.filter(amount__lt=0).aggregate(s=Sum("amount"))["s"] or 0
        return stat_grid(
            [
                ("Solde", obj.aura_balance),
                ("Crédits cumulés", credits),
                ("Débits cumulés", abs(debits)),
                ("Mouvements", entries.count()),
            ]
        )


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
    list_display = (
        "user",
        "aura_amount",
        "fee_aura",
        "fiat_amount",
        "destination_provider",
        "destination_phone",
        "status",
        "created_at",
    )
    list_filter = ("status", "destination_provider", "created_at")
    search_fields = ("user__username", "destination_phone")
    date_hierarchy = "created_at"
    list_select_related = ("user",)
    list_per_page = 50
    readonly_fields = (
        "user",
        "aura_amount",
        "fee_aura",
        "fiat_amount",
        "currency",
        "destination_provider",
        "destination_phone",
        "status",
        "idempotency_key",
        "created_at",
        "resolved_at",
    )
    actions = ("mark_processing", "mark_paid", "mark_failed")

    @admin.action(description="Marquer « versement en cours »")
    def mark_processing(self, request, queryset):
        self._resolve(request, queryset, "processing")

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
    list_display = (
        "user",
        "aura_amount",
        "destination_provider",
        "consumed",
        "created_at",
        "expires_at",
    )
    list_filter = ("consumed", "created_at")
    search_fields = ("user__username",)
    date_hierarchy = "created_at"
    readonly_fields = ("user", "aura_amount", "code_hash", "created_at", "expires_at")


@admin.register(PlatformRevenue)
class PlatformRevenueAdmin(admin.ModelAdmin):
    """Commissions perçues (lecture seule : écrites par les services de paiement)."""

    list_display = ("source", "amount_aura", "user", "related_type", "related_id", "created_at")
    list_filter = ("source", "created_at")
    search_fields = ("user__username",)
    date_hierarchy = "created_at"
    list_select_related = ("user",)
    list_per_page = 100

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
