"""Monétisation "Aura" : portefeuille, grand livre, achats, tips (70/30), payouts.

Règles :
- `LedgerEntry` est append-only et seule source de vérité des mouvements ; le
  solde `Wallet.aura_balance` en est le cache (cf. `manage.py reconcile_wallets`).
- Chaque commission plateforme est tracée dans `PlatformRevenue` (même
  transaction que le mouvement) : tip, abonnement, achat streamer, retrait.
- Les clés d'idempotence sont scopées par utilisateur.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet"
    )
    aura_balance = models.PositiveIntegerField(default=0)
    # Gel des retraits (rétrofacturation non couverte, suspicion de fraude…).
    payout_hold = models.BooleanField(default=False)
    payout_hold_reason = models.CharField(max_length=255, blank=True)
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
        PAYOUT_REVERSAL = "payout_reversal", "Retrait annulé"
        REFERRAL = "referral", "Parrainage"
        ADJUSTMENT = "adjustment", "Ajustement admin"
        CHARITY_DONATION = "charity_donation", "Don caritatif"
        REFUND = "refund", "Remboursement d'achat"

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

    def save(self, *args, **kwargs):
        """Une seule règle active par produit : activer celle-ci désactive les autres."""
        from django.db import transaction

        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.is_active:
                FeeRule.objects.filter(product=self.product, is_active=True).exclude(
                    pk=self.pk
                ).update(is_active=False)

    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if self.value is not None and self.value < 0:
            raise ValidationError({"value": "La commission ne peut pas être négative."})
        if self.mode == self.Mode.PERCENTAGE and self.value is not None and self.value > 100:
            raise ValidationError({"value": "Un pourcentage ne peut pas dépasser 100."})


class PlatformRevenue(models.Model):
    """Commission perçue par la plateforme (écrite dans la transaction du flux)."""

    class Source(models.TextChoices):
        TIP = "tip", "Tip"
        SUBSCRIPTION = "subscription", "Abonnement"
        PURCHASE = "purchase", "Achat (streamer)"
        WITHDRAWAL = "withdrawal", "Frais de retrait"

    source = models.CharField(max_length=16, choices=Source.choices, db_index=True)
    amount_aura = models.PositiveIntegerField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Utilisateur à l'origine du flux (payeur ou créateur qui retire).",
    )
    related_type = models.CharField(max_length=32, blank=True)
    related_id = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"revenue:{self.source}:{self.amount_aura}"


class IdempotencyRecord(models.Model):
    """Résultat d'une opération idempotente hors modèles dédiés (ex. abonnement)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="idempotency_records"
    )
    scope = models.CharField(max_length=32)
    key = models.CharField(max_length=64)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "scope", "key"], name="uniq_idempotency_record")
        ]

    def __str__(self) -> str:
        return f"idem:{self.user_id}:{self.scope}:{self.key}"


def _user_key_constraint(field: str, name: str) -> models.UniqueConstraint:
    """Clé d'idempotence unique PAR utilisateur (une clé d'autrui ne renvoie rien)."""
    return models.UniqueConstraint(
        fields=[field, "idempotency_key"],
        condition=models.Q(idempotency_key__isnull=False),
        name=name,
    )


class Purchase(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        PAID = "paid", "Payé"
        FAILED = "failed", "Échoué"
        REFUNDED = "refunded", "Remboursé"
        DISPUTED = "disputed", "Contesté"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="purchases"
    )
    credits = models.PositiveIntegerField()  # Aura achetés
    fiat_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8, default="XOF")
    provider = models.CharField(max_length=20)
    provider_ref = models.CharField(max_length=255, blank=True)
    # Référence du paiement chez le prestataire (ex. Stripe payment_intent), pour
    # rapprocher remboursements et litiges.
    provider_payment_ref = models.CharField(max_length=255, blank=True, db_index=True)
    status = models.CharField(
        max_length=8, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    idempotency_key = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [_user_key_constraint("user", "uniq_purchase_user_idem")]

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
    idempotency_key = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [_user_key_constraint("from_user", "uniq_tip_user_idem")]

    def __str__(self) -> str:
        return f"tip:{self.aura_amount}→{self.to_channel_id}"


class PayoutDestination(models.TextChoices):
    WAVE = "wave", "Wave"
    ORANGE_MONEY = "orange_money", "Orange Money"


class PayoutOtp(models.Model):
    """Code OTP à usage unique confirmant une demande de retrait."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payout_otps"
    )
    aura_amount = models.PositiveIntegerField()
    destination_provider = models.CharField(
        max_length=16, choices=PayoutDestination.choices, blank=True
    )
    destination_phone = models.CharField(max_length=20, blank=True)
    code_hash = models.CharField(max_length=64)
    consumed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"payout-otp:{self.user_id}:{self.aura_amount}"


class Payout(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Demandé"
        PROCESSING = "processing", "En cours de versement"
        PAID = "paid", "Payé"
        FAILED = "failed", "Échoué"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payouts"
    )
    aura_amount = models.PositiveIntegerField()  # Aura débités (brut)
    fee_aura = models.PositiveIntegerField(default=0)  # frais de traitement
    fiat_amount = models.DecimalField(max_digits=10, decimal_places=2)  # net versé (XOF)
    currency = models.CharField(max_length=8, default="XOF")
    destination_provider = models.CharField(
        max_length=16, choices=PayoutDestination.choices, blank=True
    )
    destination_phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.REQUESTED, db_index=True
    )
    idempotency_key = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [_user_key_constraint("user", "uniq_payout_user_idem")]

    def __str__(self) -> str:
        return f"payout:{self.aura_amount}:{self.status}"
