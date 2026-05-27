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
        PAYOUT = "payout", "Retrait"

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="entries")
    amount = models.IntegerField()  # Aura signé
    kind = models.CharField(max_length=16, choices=Kind.choices)
    reference = models.CharField(max_length=255, blank=True)
    balance_after = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.kind}:{self.amount}"


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
    currency = models.CharField(max_length=8, default="EUR")
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
    currency = models.CharField(max_length=8, default="EUR")
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.REQUESTED, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"payout:{self.aura_amount}:{self.status}"
