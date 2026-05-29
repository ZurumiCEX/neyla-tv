"""Logique métier monétisation : ledger atomique, achat, tip (70/30), payout."""

from __future__ import annotations

import contextlib
import decimal

from django.conf import settings
from django.db import transaction

from .models import FeeRule, LedgerEntry, Payout, Purchase, Tip, Wallet
from .providers import get_provider, get_provider_name


class PaymentError(Exception):
    """Erreur métier paiements."""


class InsufficientBalanceError(PaymentError):
    """Solde Aura insuffisant."""


def split(amount: int, product: str) -> tuple[int, int]:
    """Répartit un montant Aura → (part créateur, commission plateforme).

    Utilise la FeeRule active du produit ; repli sur CREATOR_SHARE si aucune règle.
    """
    amount = int(amount)
    rule = FeeRule.objects.filter(product=product, is_active=True).order_by("-created_at").first()
    if rule is None:
        creator_share = int(amount * float(getattr(settings, "CREATOR_SHARE", 0.70)))
        return creator_share, amount - creator_share
    if rule.mode == FeeRule.Mode.FIXED:
        platform_fee = int(rule.value)
    else:
        platform_fee = int(amount * float(rule.value) / 100)
    platform_fee = max(0, min(platform_fee, amount))
    return amount - platform_fee, platform_fee


def aura_unit_price() -> decimal.Decimal:
    """Prix d'1 Aura en XOF (FCFA)."""
    return decimal.Decimal(str(getattr(settings, "AURA_UNIT_PRICE_XOF", "5")))


def _fiat_for(credits: int) -> decimal.Decimal:
    """Montant en XOF (sans décimale) pour un nombre d'Aura."""
    return (aura_unit_price() * credits).quantize(decimal.Decimal("1"))


def get_wallet(user) -> Wallet:
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


def _apply(
    wallet: Wallet,
    amount: int,
    kind: str,
    reference: str = "",
    related=None,
    metadata: dict | None = None,
) -> None:
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
        related_type=related.__class__.__name__.lower() if related is not None else "",
        related_id=getattr(related, "id", None),
        metadata=metadata or {},
    )


@transaction.atomic
def grant_aura(user, amount: int, kind: str, reference: str = "", metadata: dict | None = None):
    """Crédite gratuitement de l'Aura à un utilisateur (parrainage, bonus…)."""
    amount = int(amount)
    if amount <= 0:
        return None
    wallet = Wallet.objects.select_for_update().get_or_create(user=user)[0]
    _apply(wallet, amount, kind, reference, metadata=metadata)
    return wallet


@transaction.atomic
def adjust_balance(actor, user, amount: int, reason: str = "") -> Wallet:
    """Ajustement manuel du solde Aura par un administrateur (tracé au ledger + audit).

    ``amount`` peut être positif (crédit) ou négatif (débit). Lève
    ``InsufficientBalanceError`` si le débit rendrait le solde négatif.
    """
    from audit.services import record

    amount = int(amount)
    if amount == 0:
        raise PaymentError("Le montant de l'ajustement ne peut pas être nul.")
    wallet = Wallet.objects.select_for_update().get_or_create(user=user)[0]
    _apply(
        wallet,
        amount,
        LedgerEntry.Kind.ADJUSTMENT,
        reference=reason[:255],
        metadata={"reason": reason, "by": getattr(actor, "username", "")},
    )
    record(
        actor,
        "wallet.adjust",
        target=user,
        meta={"amount": amount, "reason": reason, "balance_after": wallet.aura_balance},
    )
    return wallet


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


def create_purchase(
    user,
    credits: int,
    currency: str = "XOF",
    idempotency_key: str | None = None,
    method: str = "",
) -> tuple[Purchase, dict]:
    credits = int(credits)
    if credits <= 0:
        raise PaymentError("Montant invalide.")
    if idempotency_key:
        existing = Purchase.objects.filter(idempotency_key=idempotency_key).first()
        if existing is not None:
            return existing, {
                "checkout_url": None,
                "auto_confirm": existing.status == Purchase.Status.PAID,
            }
    from .providers import method_to_provider

    provider_name = method_to_provider(method) if method else get_provider_name()
    purchase = Purchase.objects.create(
        user=user,
        credits=credits,
        fiat_amount=_fiat_for(credits),
        currency=currency,
        provider=provider_name,
        idempotency_key=idempotency_key or None,
    )
    result = get_provider(provider_name).create_checkout(purchase)
    purchase.provider_ref = result.get("provider_ref", "")
    purchase.save(update_fields=["provider_ref"])
    if result.get("auto_confirm"):
        confirm_purchase(purchase)
        purchase.refresh_from_db()
    return purchase, result


@transaction.atomic
def send_tip(
    from_user,
    channel_slug: str,
    aura_amount: int,
    message: str = "",
    idempotency_key: str | None = None,
) -> Tip:
    from channels_app.models import Channel

    aura_amount = int(aura_amount)
    if aura_amount <= 0:
        raise PaymentError("Montant invalide.")
    if idempotency_key:
        existing = Tip.objects.filter(idempotency_key=idempotency_key).first()
        if existing is not None:
            return existing
    channel = Channel.objects.select_related("user").filter(slug=channel_slug.lower()).first()
    if channel is None:
        raise PaymentError("Chaîne introuvable.")
    if channel.user_id == from_user.id:
        raise PaymentError("Tu ne peux pas te tipper toi-même.")

    sender = Wallet.objects.select_for_update().get_or_create(user=from_user)[0]
    if sender.aura_balance < aura_amount:
        raise InsufficientBalanceError("Solde Aura insuffisant.")

    creator_share, platform_fee = split(aura_amount, FeeRule.Product.TIP)

    _apply(sender, -aura_amount, LedgerEntry.Kind.TIP_SENT, f"channel:{channel.slug}")
    creator_wallet = Wallet.objects.select_for_update().get_or_create(user=channel.user)[0]
    _apply(
        creator_wallet,
        creator_share,
        LedgerEntry.Kind.TIP_RECEIVED,
        f"from:{from_user.username}",
    )
    tip = Tip.objects.create(
        from_user=from_user,
        to_channel=channel,
        aura_amount=aura_amount,
        creator_share=creator_share,
        platform_fee=platform_fee,
        message=message[:200],
        idempotency_key=idempotency_key or None,
    )
    _after_tip(tip, from_user, channel)
    return tip


def _after_tip(tip: Tip, from_user, channel) -> None:
    """Notification au créateur + succès (best-effort, hors transaction critique)."""
    from notifications.models import Notification
    from notifications.services import create_notification

    create_notification(
        recipient=channel.user,
        type=Notification.Type.TIP_RECEIVED,
        actor=from_user,
        payload={
            "username": from_user.username,
            "aura": tip.creator_share,
            "slug": channel.slug,
        },
    )
    from gamification.services import check_and_award

    check_and_award(from_user, "tip_sent")
    check_and_award(channel.user, "tip_received")

    with contextlib.suppress(Exception):
        from safety.anticheat import evaluate_self_deal, evaluate_tip

        evaluate_tip(from_user, channel)
        evaluate_self_deal(from_user, channel)


@transaction.atomic
def request_payout(
    user, aura_amount: int, idempotency_key: str | None = None, fee_pct: float = 0.0
) -> Payout:
    aura_amount = int(aura_amount)
    if aura_amount <= 0:
        raise PaymentError("Montant invalide.")
    if idempotency_key:
        existing = Payout.objects.filter(idempotency_key=idempotency_key).first()
        if existing is not None:
            return existing
    wallet = Wallet.objects.select_for_update().get_or_create(user=user)[0]
    if wallet.aura_balance < aura_amount:
        raise InsufficientBalanceError("Solde Aura insuffisant.")
    _apply(wallet, -aura_amount, LedgerEntry.Kind.PAYOUT, "payout")
    # Le montant fiat versé est net de la commission de retrait (part créateur).
    fee_pct = max(0.0, min(float(fee_pct), 1.0))
    net_fiat = _fiat_for(aura_amount) * decimal.Decimal(str(1.0 - fee_pct))
    payout = Payout.objects.create(
        user=user,
        aura_amount=aura_amount,
        fiat_amount=net_fiat.quantize(decimal.Decimal("0.01")),
        idempotency_key=idempotency_key or None,
    )
    from audit.services import record

    record(user, "payout.request", target=payout, meta={"aura": aura_amount, "fee_pct": fee_pct})
    return payout


# --- Retrait : éligibilité, solde retirable, devis, OTP -----------------------

WITHDRAWAL_OTP_TTL_MIN = 10


def is_eligible_streamer(user) -> bool:
    """Seuls les streamers approuvés (chaîne provisionnée) peuvent retirer."""
    channel = getattr(user, "channel", None)
    return bool(channel and channel.is_provisioned)


def withdrawable_balance(user) -> int:
    """Aura retirable = reçue des utilisateurs (tips + abonnements), hors achats,
    diminuée des retraits déjà demandés, plafonnée par le solde courant."""
    from django.db.models import Sum

    earned = (
        LedgerEntry.objects.filter(
            wallet__user=user,
            kind__in=[LedgerEntry.Kind.TIP_RECEIVED, LedgerEntry.Kind.SUB_EARNED],
        ).aggregate(s=Sum("amount"))["s"]
        or 0
    )
    withdrawn = (
        Payout.objects.filter(user=user)
        .exclude(status=Payout.Status.FAILED)
        .aggregate(s=Sum("aura_amount"))["s"]
        or 0
    )
    available = int(earned) - int(withdrawn)
    balance = get_wallet(user).aura_balance
    return max(0, min(available, balance))


def withdrawal_fee_pct() -> float:
    return float(getattr(settings, "WITHDRAWAL_FEE_PCT", 0.30))


def withdrawal_quote(aura_amount: int) -> dict:
    aura_amount = max(0, int(aura_amount))
    fee_pct = withdrawal_fee_pct()
    fee_aura = int(aura_amount * fee_pct)
    net_aura = aura_amount - fee_aura
    return {
        "aura": aura_amount,
        "fee_pct": round(fee_pct * 100),
        "fee_aura": fee_aura,
        "net_aura": net_aura,
        "net_fiat": str(_fiat_for(net_aura)),
        "currency": "XOF",
    }


def start_withdrawal(user, aura_amount: int):
    """Valide la demande et émet un code OTP (envoyé hors-bande)."""
    import secrets

    from .models import PayoutOtp

    if not is_eligible_streamer(user):
        raise PaymentError("Seuls les streamers approuvés peuvent demander un retrait.")
    aura_amount = int(aura_amount)
    if aura_amount <= 0:
        raise PaymentError("Montant invalide.")
    if aura_amount > withdrawable_balance(user):
        raise InsufficientBalanceError("Montant supérieur à ton solde retirable.")
    from django.utils import timezone

    # Invalide les OTP en attente précédents.
    PayoutOtp.objects.filter(user=user, consumed=False).update(consumed=True)
    code = f"{secrets.randbelow(1_000_000):06d}"
    otp = PayoutOtp.objects.create(
        user=user,
        aura_amount=aura_amount,
        code_hash=_hash_otp(code),
        expires_at=timezone.now() + timezone.timedelta(minutes=WITHDRAWAL_OTP_TTL_MIN),
    )
    _send_withdrawal_otp(user, code)
    return otp


def confirm_withdrawal(user, code: str) -> Payout:
    """Vérifie l'OTP puis crée le retrait (commission plateforme appliquée)."""
    from django.utils import timezone

    from .models import PayoutOtp

    otp = (
        PayoutOtp.objects.filter(user=user, consumed=False, expires_at__gte=timezone.now())
        .order_by("-created_at")
        .first()
    )
    if otp is None or not _verify_otp(otp.code_hash, code):
        raise PaymentError("Code de vérification invalide ou expiré.")
    otp.consumed = True
    otp.save(update_fields=["consumed"])
    return request_payout(user, otp.aura_amount, fee_pct=withdrawal_fee_pct())


def _hash_otp(code: str) -> str:
    import hashlib

    return hashlib.sha256(code.encode()).hexdigest()


def _verify_otp(code_hash: str, code: str) -> bool:
    import hmac as _hmac

    return _hmac.compare_digest(code_hash, _hash_otp((code or "").strip()))


def _send_withdrawal_otp(user, code: str) -> None:
    """Envoie le code par email + notification in-app (best-effort)."""
    ttl = WITHDRAWAL_OTP_TTL_MIN
    with contextlib.suppress(Exception):
        from django.conf import settings as _s
        from django.core.mail import send_mail

        send_mail(
            subject="Code de confirmation de retrait — Neyla TV",
            message=f"Ton code de confirmation de retrait est : {code}\nValable {ttl} minutes.",
            from_email=_s.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    with contextlib.suppress(Exception):
        from notifications.services import send_support_message

        send_support_message(
            user,
            "Confirmation de retrait",
            f"Ton code de confirmation est : {code} (valable {ttl} min).",
        )


@transaction.atomic
def charge_subscription(payer, creator, amount: int) -> tuple[int, int]:
    """Débite l'abonné en Aura et crédite le créateur (split fee). Retourne (part, commission)."""
    amount = int(amount)
    if amount <= 0:
        raise PaymentError("Montant invalide.")
    wallet = Wallet.objects.select_for_update().get_or_create(user=payer)[0]
    if wallet.aura_balance < amount:
        raise InsufficientBalanceError("Solde Aura insuffisant.")
    creator_share, platform_fee = split(amount, FeeRule.Product.SUBSCRIPTION)
    _apply(wallet, -amount, LedgerEntry.Kind.SUB_PAID, f"sub:{creator.username}")
    creator_wallet = Wallet.objects.select_for_update().get_or_create(user=creator)[0]
    _apply(creator_wallet, creator_share, LedgerEntry.Kind.SUB_EARNED, f"sub-from:{payer.username}")
    return creator_share, platform_fee


def list_transactions(type_filter: str = "", query: str = "", days: int = 0) -> list[dict]:
    """Flux unifié Purchase/Tip/Subscription/Payout (récent d'abord) pour l'admin."""
    from django.utils import timezone

    since = None
    if days and days > 0:
        since = timezone.now() - timezone.timedelta(days=days)
    rows: list[dict] = []
    want = type_filter or "all"
    q = (query or "").strip().lower()

    if want in ("all", "purchase"):
        qs = Purchase.objects.select_related("user").all()
        if since:
            qs = qs.filter(created_at__gte=since)
        if q:
            qs = qs.filter(user__username__icontains=q)
        for p in qs[:500]:
            rows.append(
                {
                    "type": "purchase",
                    "id": p.id,
                    "user": p.user.username,
                    "aura": p.credits,
                    "fiat_amount": str(p.fiat_amount),
                    "currency": p.currency,
                    "status": p.status,
                    "created_at": p.created_at,
                    "detail": f"{p.credits} Aura via {p.provider}",
                }
            )
    if want in ("all", "tip"):
        qs = Tip.objects.select_related("from_user", "to_channel").all()
        if since:
            qs = qs.filter(created_at__gte=since)
        if q:
            qs = qs.filter(from_user__username__icontains=q)
        for t in qs[:500]:
            rows.append(
                {
                    "type": "tip",
                    "id": t.id,
                    "user": t.from_user.username,
                    "aura": t.aura_amount,
                    "platform_fee": t.platform_fee,
                    "status": "paid",
                    "created_at": t.created_at,
                    "detail": f"→ @{t.to_channel.slug} (part créateur {t.creator_share})",
                }
            )
    if want in ("all", "subscription"):
        from subscriptions.models import Subscription

        qs = Subscription.objects.select_related("subscriber", "channel", "tier").all()
        if since:
            qs = qs.filter(created_at__gte=since)
        if q:
            qs = qs.filter(subscriber__username__icontains=q)
        for s in qs[:500]:
            rows.append(
                {
                    "type": "subscription",
                    "id": s.id,
                    "user": s.subscriber.username,
                    "aura": s.tier.price_aura if s.tier else 0,
                    "status": s.status,
                    "created_at": s.created_at,
                    "detail": f"→ @{s.channel.slug}",
                }
            )
    if want in ("all", "payout"):
        qs = Payout.objects.select_related("user").all()
        if since:
            qs = qs.filter(created_at__gte=since)
        if q:
            qs = qs.filter(user__username__icontains=q)
        for p in qs[:500]:
            rows.append(
                {
                    "type": "payout",
                    "id": p.id,
                    "user": p.user.username,
                    "aura": p.aura_amount,
                    "fiat_amount": str(p.fiat_amount),
                    "currency": p.currency,
                    "status": p.status,
                    "created_at": p.created_at,
                    "detail": f"{p.fiat_amount} {p.currency}",
                }
            )

    rows.sort(key=lambda r: r["created_at"], reverse=True)
    return rows


@transaction.atomic
def resolve_payout(admin, payout: Payout, action: str) -> Payout:
    """Action admin sur un retrait : `paid` (validé) ou `fail` (rejeté → remboursé)."""
    if action not in ("paid", "fail"):
        raise PaymentError("Action invalide.")
    if payout.status != Payout.Status.REQUESTED:
        raise PaymentError("Ce retrait a déjà été traité.")
    if action == "paid":
        payout.status = Payout.Status.PAID
        payout.save(update_fields=["status"])
    else:
        wallet = Wallet.objects.select_for_update().get_or_create(user=payout.user)[0]
        _apply(
            wallet,
            payout.aura_amount,
            LedgerEntry.Kind.PAYOUT,
            "payout-refund",
            related=payout,
            metadata={"refund": True},
        )
        payout.status = Payout.Status.FAILED
        payout.save(update_fields=["status"])
    from audit.services import record

    record(admin, f"payout.{action}", target=payout, meta={"aura": payout.aura_amount})
    return payout
