"""Logique métier monétisation : ledger atomique, achat, tip (70/30), payout."""

from __future__ import annotations

import decimal

from django.conf import settings
from django.db import transaction

from .models import LedgerEntry, Payout, Purchase, Tip, Wallet
from .providers import get_provider, get_provider_name


class PaymentError(Exception):
    """Erreur métier paiements."""


class InsufficientBalanceError(PaymentError):
    """Solde Aura insuffisant."""


def aura_unit_price() -> decimal.Decimal:
    """Prix d'1 Aura en XOF (FCFA)."""
    return decimal.Decimal(str(getattr(settings, "AURA_UNIT_PRICE_XOF", "5")))


def _fiat_for(credits: int) -> decimal.Decimal:
    """Montant en XOF (sans décimale) pour un nombre d'Aura."""
    return (aura_unit_price() * credits).quantize(decimal.Decimal("1"))


def get_wallet(user) -> Wallet:
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


def _apply(wallet: Wallet, amount: int, kind: str, reference: str = "") -> None:
    """Applique une variation de solde + écriture ledger. Lève si solde négatif."""
    new_balance = wallet.aura_balance + amount
    if new_balance < 0:
        raise InsufficientBalanceError("Solde Aura insuffisant.")
    wallet.aura_balance = new_balance
    wallet.save(update_fields=["aura_balance"])
    LedgerEntry.objects.create(
        wallet=wallet,
        amount=amount,
        kind=kind,
        reference=reference,
        balance_after=new_balance,
    )


@transaction.atomic
def confirm_purchase(purchase: Purchase) -> Purchase:
    """Idempotent : crédite le wallet une seule fois (anti-rejeu webhook)."""
    if purchase.status == Purchase.Status.PAID:
        return purchase
    purchase.status = Purchase.Status.PAID
    purchase.save(update_fields=["status"])
    wallet = Wallet.objects.select_for_update().get_or_create(user=purchase.user)[0]
    _apply(wallet, purchase.credits, LedgerEntry.Kind.PURCHASE, f"purchase:{purchase.id}")
    return purchase


def create_purchase(user, credits: int, currency: str = "XOF") -> tuple[Purchase, dict]:
    credits = int(credits)
    if credits <= 0:
        raise PaymentError("Montant invalide.")
    purchase = Purchase.objects.create(
        user=user,
        credits=credits,
        fiat_amount=_fiat_for(credits),
        currency=currency,
        provider=get_provider_name(),
    )
    result = get_provider().create_checkout(purchase)
    purchase.provider_ref = result.get("provider_ref", "")
    purchase.save(update_fields=["provider_ref"])
    if result.get("auto_confirm"):
        confirm_purchase(purchase)
        purchase.refresh_from_db()
    return purchase, result


@transaction.atomic
def send_tip(from_user, channel_slug: str, aura_amount: int, message: str = "") -> Tip:
    from channels_app.models import Channel

    aura_amount = int(aura_amount)
    if aura_amount <= 0:
        raise PaymentError("Montant invalide.")
    channel = Channel.objects.select_related("user").filter(slug=channel_slug.lower()).first()
    if channel is None:
        raise PaymentError("Chaîne introuvable.")
    if channel.user_id == from_user.id:
        raise PaymentError("Tu ne peux pas te tipper toi-même.")

    sender = Wallet.objects.select_for_update().get_or_create(user=from_user)[0]
    if sender.aura_balance < aura_amount:
        raise InsufficientBalanceError("Solde Aura insuffisant.")

    creator_share = int(aura_amount * float(getattr(settings, "CREATOR_SHARE", 0.70)))
    platform_fee = aura_amount - creator_share

    _apply(sender, -aura_amount, LedgerEntry.Kind.TIP_SENT, f"channel:{channel.slug}")
    creator_wallet = Wallet.objects.select_for_update().get_or_create(user=channel.user)[0]
    _apply(
        creator_wallet,
        creator_share,
        LedgerEntry.Kind.TIP_RECEIVED,
        f"from:{from_user.username}",
    )
    return Tip.objects.create(
        from_user=from_user,
        to_channel=channel,
        aura_amount=aura_amount,
        creator_share=creator_share,
        platform_fee=platform_fee,
        message=message[:200],
    )


@transaction.atomic
def request_payout(user, aura_amount: int) -> Payout:
    aura_amount = int(aura_amount)
    if aura_amount <= 0:
        raise PaymentError("Montant invalide.")
    wallet = Wallet.objects.select_for_update().get_or_create(user=user)[0]
    if wallet.aura_balance < aura_amount:
        raise InsufficientBalanceError("Solde Aura insuffisant.")
    _apply(wallet, -aura_amount, LedgerEntry.Kind.PAYOUT, "payout")
    return Payout.objects.create(
        user=user, aura_amount=aura_amount, fiat_amount=_fiat_for(aura_amount)
    )
