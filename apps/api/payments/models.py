"""Monétisation "Aura" : portefeuille, grand livre, achats, tips (70/30), payouts."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet"
    )
    aura_balance = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"wallet:{self.user_id}:{self.aura_balance}"


class LedgerEntry(models.Model):
    """Écriture append-only du grand livre Aura."""

    class Kind(models.TextChoices):
        PURCHASE = "purchase", "Achat"
        TIP_SENT = "tip_sent", "Tip envoyé"
        TIP_RECEIVED = "tip_received", "Tip reçu"
        SUB_PAID = "sub_paid", "Abonnement payé"
        SUB_EARNED = "sub_earned", "Abonnement reçu"
        PAYOUT = "payout", "Retrait"

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="entries")
    amount = models.IntegerField()  # Aura signé
    kind = models.CharField(max_length=16, choices=Kind.choices)
    reference = models.CharField(max_length=255, blank=True)
    balance_after = models.IntegerField()
    currency = models.CharField(max_length=8, default="AURA")
    related_type = models.CharField(max_length=32, blank=True)
    related_id = models.PositiveBigIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.kind}:{self.amount}"


class FeeRule(models.Model):
    """Règle de commission plateforme par produit (remplace CREATOR_SHARE figé)."""

    class Product(models.TextChoices):
        TIP = "tip", "Tip"
        SUBSCRIPTION = "subscription", "Abonnement"
        PURCHASE = "purchase", "Achat"

    class Mode(models.TextChoices):
        PERCENTAGE = "percentage", "Pourcentage"
        FIXED = "fixed", "Montant fixe"

    product = models.CharField(max_length=16, choices=Product.choices, db_index=True)
    mode = models.CharField(max_length=12, choices=Mode.choices, default=Mode.PERCENTAGE)
    value = models.DecimalField(max_digits=9, decimal_places=2)  # commission plateforme
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["product", "-created_at"]

    def __str__(self) -> str:
        return f"fee:{self.product}:{self.mode}:{self.value}"


class Purchase(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        PAID = "paid", "Payé"
        FAILED = "failed", "Échoué"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="purchases"
    )
    credits = models.PositiveIntegerField()  # Aura achetés
    fiat_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8, default="XOF")
    provider = models.CharField(max_length=20)
    provider_ref = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=8, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"purchase:{self.id}:{self.status}"


class Tip(models.Model):
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tips_sent"
    )
    to_channel = models.ForeignKey(
        "channels_app.Channel", on_delete=models.CASCADE, related_name="tips"
    )
    aura_amount = models.PositiveIntegerField()
    creator_share = models.PositiveIntegerField()
    platform_fee = models.PositiveIntegerField()
    message = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"tip:{self.aura_amount}→{self.to_channel_id}"


class Payout(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Demandé"
        PAID = "paid", "Payé"
        FAILED = "failed", "Échoué"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payouts"
    )
    aura_amount = models.PositiveIntegerField()
    fiat_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8, default="XOF")
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.REQUESTED, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"payout:{self.aura_amount}:{self.status}"
