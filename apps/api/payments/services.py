"""Logique métier monétisation Aura : ledger atomique, achat, tip, abonnement, retrait.

Invariants :
- Toute écriture de solde passe par `_apply` (ledger append-only + cache solde).
- Les wallets sont verrouillés via `_lock_wallets` (ordre stable par user_id →
  pas d'interblocage A→B / B→A) dans la transaction du mouvement.
- Chaque commission est tracée dans `PlatformRevenue` dans la même transaction.
- Un seul prélèvement par flux : 30 % sur tips/abonnements (créateur), 1 % sur
  l'achat d'Aura d'un streamer, et des frais de traitement au retrait.
- Seule l'Aura **gagnée** (tips + abonnements reçus) est retirable : l'Aura
  achetée ou offerte (parrainage, bonus) ne se convertit jamais en argent.
"""

from __future__ import annotations

import contextlib
import decimal
import logging
import re

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone

from .models import (
    FeeRule,
    IdempotencyRecord,
    LedgerEntry,
    Payout,
    PayoutDestination,
    PlatformRevenue,
    Purchase,
    Tip,
    Wallet,
)
from .providers import get_provider, get_provider_name, simulated_payments_allowed

logger = logging.getLogger(__name__)

ROUND = decimal.ROUND_HALF_UP


class PaymentError(Exception):
    """Erreur métier paiements."""


class InsufficientBalanceError(PaymentError):
    """Solde Aura insuffisant."""


# --- Paramètres ---------------------------------------------------------------


def tip_min_aura() -> int:
    return int(getattr(settings, "TIP_MIN_AURA", 10))


def withdrawal_min_aura() -> int:
    return int(getattr(settings, "WITHDRAWAL_MIN_AURA", 1000))


def withdrawal_fee_pct() -> float:
    """Frais de traitement d'un retrait (fraction, ex. 0.03)."""
    pct = float(getattr(settings, "WITHDRAWAL_PROCESSING_FEE_PCT", 0.03))
    return max(0.0, min(pct, 1.0))


def aura_unit_price() -> decimal.Decimal:
    """Prix d'1 Aura en XOF (FCFA)."""
    return decimal.Decimal(str(getattr(settings, "AURA_UNIT_PRICE_XOF", "5")))


def _fiat_for(credits: int) -> decimal.Decimal:
    """Montant en XOF (entier : le FCFA n'a pas de centimes) pour un nombre d'Aura."""
    return (aura_unit_price() * int(credits)).quantize(decimal.Decimal("1"), rounding=ROUND)


def _pct_of(amount: int, pct: decimal.Decimal | float | str) -> int:
    """Arrondi commercial (demi supérieur) de `amount × pct / 100`."""
    value = decimal.Decimal(int(amount)) * decimal.Decimal(str(pct)) / 100
    return int(value.quantize(decimal.Decimal("1"), rounding=ROUND))


def split(amount: int, product: str) -> tuple[int, int]:
    """Répartit un montant Aura → (part créateur, commission plateforme).

    Utilise LA règle active du produit ; repli sur CREATOR_SHARE si aucune.
    La commission est arrondie au demi supérieur (un tip de 3 Aura à 30 %
    rapporte 1 Aura à la plateforme, plus 0 comme auparavant).
    """
    amount = int(amount)
    rule = FeeRule.objects.filter(product=product, is_active=True).order_by("-created_at").first()
    if rule is None:
        share = decimal.Decimal(str(getattr(settings, "CREATOR_SHARE", 0.70)))
        platform_fee = _pct_of(amount, (1 - share) * 100)
    elif rule.mode == FeeRule.Mode.FIXED:
        platform_fee = int(rule.value)
    else:
        platform_fee = _pct_of(amount, rule.value)
    platform_fee = max(0, min(platform_fee, amount))
    return amount - platform_fee, platform_fee


# --- Wallets & ledger ----------------------------------------------------------


def get_wallet(user) -> Wallet:
    """Wallet de l'utilisateur (créé au besoin, sûr en concurrence)."""
    try:
        with transaction.atomic():
            wallet, _ = Wallet.objects.get_or_create(user=user)
    except IntegrityError:  # créé en parallèle
        wallet = Wallet.objects.get(user=user)
    return wallet


def _lock_wallets(*users) -> dict[int, Wallet]:
    """Verrouille (SELECT … FOR UPDATE) les wallets donnés, triés par user_id.

    À appeler DANS une transaction. L'ordre stable évite les interblocages
    quand deux utilisateurs se tippent mutuellement au même instant.
    """
    ids = sorted({u.pk for u in users})
    for user in users:
        get_wallet(user)
    locked = Wallet.objects.select_for_update().filter(user_id__in=ids).order_by("user_id")
    return {w.user_id: w for w in locked}


def _apply(
    wallet: Wallet,
    amount: int,
    kind: str,
    reference: str = "",
    related=None,
    metadata: dict | None = None,
) -> None:
    """Applique une variation de solde + écriture ledger. Lève si solde négatif.

    Le wallet DOIT être verrouillé par l'appelant (`_lock_wallets`).
    """
    new_balance = wallet.aura_balance + int(amount)
    if new_balance < 0:
        raise InsufficientBalanceError("Solde Aura insuffisant.")
    wallet.aura_balance = new_balance
    wallet.save(update_fields=["aura_balance"])
    LedgerEntry.objects.create(
        wallet=wallet,
        amount=int(amount),
        kind=kind,
        reference=reference[:255],
        balance_after=new_balance,
        related_type=related.__class__.__name__.lower() if related is not None else "",
        related_id=getattr(related, "id", None),
        metadata=metadata or {},
    )


def _record_fee(source: str, amount: int, user=None, related=None) -> None:
    if int(amount) <= 0:
        return
    PlatformRevenue.objects.create(
        source=source,
        amount_aura=int(amount),
        user=user,
        related_type=related.__class__.__name__.lower() if related is not None else "",
        related_id=getattr(related, "id", None),
    )


def remember(user, scope: str, key: str | None, obj) -> None:
    """Mémorise le résultat d'une opération idempotente (user, scope, key)."""
    if key:
        IdempotencyRecord.objects.get_or_create(
            user=user, scope=scope, key=key, defaults={"object_id": obj.pk}
        )


def recall(user, scope: str, key: str | None):
    """ID d'objet déjà produit pour (user, scope, key), sinon None."""
    if not key:
        return None
    rec = IdempotencyRecord.objects.filter(user=user, scope=scope, key=key).first()
    return rec.object_id if rec else None


@transaction.atomic
def grant_aura(user, amount: int, kind: str, reference: str = "", metadata: dict | None = None):
    """Crédite gratuitement de l'Aura à un utilisateur (parrainage, bonus…).

    Cette Aura n'est PAS retirable (cf. `withdrawable_balance`).
    """
    amount = int(amount)
    if amount <= 0:
        return None
    wallet = _lock_wallets(user)[user.pk]
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
    wallet = _lock_wallets(user)[user.pk]
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


def _is_streamer(user) -> bool:
    """True si l'utilisateur est un streamer approuvé (requête fraîche)."""
    from channels_app.utils import is_streamer

    return is_streamer(user)


# --- Achat d'Aura ---------------------------------------------------------------


@transaction.atomic
def confirm_purchase(purchase: Purchase) -> Purchase:
    """Crédite le wallet UNE seule fois, même sous webhooks concurrents.

    La ligne d'achat est verrouillée puis basculée PENDING → PAID : un second
    appel (rejeu Stripe, double clic) ne crédite rien.

    Business model :
    - Viewer : 1 Aura acheté = 1 Aura crédité (aucune commission).
    - Streamer : commission `FeeRule.PURCHASE` (1 % par défaut) prélevée sur
      l'Aura crédité. Seul prélèvement côté achat.
    """
    locked = Purchase.objects.select_for_update().get(pk=purchase.pk)
    if locked.status != Purchase.Status.PENDING:
        return locked
    locked.status = Purchase.Status.PAID
    locked.save(update_fields=["status"])

    credits = int(locked.credits)
    fee = 0
    if _is_streamer(locked.user):
        credited, fee = split(credits, FeeRule.Product.PURCHASE)
    else:
        credited = credits
    wallet = _lock_wallets(locked.user)[locked.user_id]
    _apply(
        wallet,
        credited,
        LedgerEntry.Kind.PURCHASE,
        f"purchase:{locked.id}",
        related=locked,
        metadata={"gross": credits, "platform_fee": fee} if fee else None,
    )
    _record_fee(PlatformRevenue.Source.PURCHASE, fee, user=locked.user, related=locked)
    return locked


def fail_purchase(purchase: Purchase) -> Purchase:
    Purchase.objects.filter(pk=purchase.pk, status=Purchase.Status.PENDING).update(
        status=Purchase.Status.FAILED
    )
    purchase.refresh_from_db()
    return purchase


@transaction.atomic
def reverse_purchase(purchase: Purchase, disputed: bool = False) -> Purchase:
    """Remboursement ou litige d'un achat payé : reprend l'Aura créditée.

    Si l'Aura a déjà été dépensée, on reprend ce qui reste, on gèle les retraits
    et on lève un signal de risque pour revue (rétrofacturation non couverte).
    """
    locked = Purchase.objects.select_for_update().get(pk=purchase.pk)
    if locked.status != Purchase.Status.PAID:
        return locked
    credited = (
        LedgerEntry.objects.filter(
            kind=LedgerEntry.Kind.PURCHASE, related_type="purchase", related_id=locked.id
        ).aggregate(s=Sum("amount"))["s"]
        or locked.credits
    )
    wallet = _lock_wallets(locked.user)[locked.user_id]
    clawback = min(int(credited), wallet.aura_balance)
    shortfall = int(credited) - clawback
    if clawback:
        _apply(
            wallet,
            -clawback,
            LedgerEntry.Kind.REFUND,
            f"purchase:{locked.id}",
            related=locked,
            metadata={"disputed": disputed, "shortfall": shortfall},
        )
    if shortfall:
        wallet.payout_hold = True
        wallet.payout_hold_reason = f"Achat #{locked.id} remboursé/contesté non couvert"
        wallet.save(update_fields=["payout_hold", "payout_hold_reason"])
        with contextlib.suppress(Exception):
            from safety.models import RiskEvent

            RiskEvent.objects.create(
                user=locked.user,
                kind=RiskEvent.Kind.CHARGEBACK,
                severity=RiskEvent.Severity.HIGH,
                detail={"purchase": locked.id, "shortfall_aura": shortfall},
            )
    locked.status = Purchase.Status.DISPUTED if disputed else Purchase.Status.REFUNDED
    locked.save(update_fields=["status"])
    return locked


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
        existing = Purchase.objects.filter(user=user, idempotency_key=idempotency_key).first()
        if existing is not None:
            return existing, {
                "checkout_url": None,
                "auto_confirm": existing.status == Purchase.Status.PAID,
            }
    from .providers import method_to_provider

    provider_name = method_to_provider(method) if method else get_provider_name()
    provider = get_provider(provider_name)
    if provider.is_simulated() and not simulated_payments_allowed():
        raise PaymentError("Ce moyen de paiement n'est pas encore disponible.")
    try:
        with transaction.atomic():
            purchase = Purchase.objects.create(
                user=user,
                credits=credits,
                fiat_amount=_fiat_for(credits),
                currency=currency,
                provider=provider_name,
                idempotency_key=idempotency_key or None,
            )
    except IntegrityError:  # même clé envoyée deux fois en parallèle
        existing = Purchase.objects.get(user=user, idempotency_key=idempotency_key)
        return existing, {"checkout_url": None, "auto_confirm": False}
    result = provider.create_checkout(purchase)
    purchase.provider_ref = result.get("provider_ref", "")
    purchase.save(update_fields=["provider_ref"])
    if result.get("auto_confirm"):
        purchase = confirm_purchase(purchase)
    return purchase, result


def handle_provider_event(provider_name: str, event: dict) -> Purchase | None:
    """Applique un événement webhook normalisé (paid / refunded / disputed)."""
    kind = event.get("event")
    if kind == "paid":
        purchase = Purchase.objects.filter(id=event.get("purchase_id") or 0).first()
        if purchase is None or purchase.provider != provider_name:
            return None
        amount, currency = event.get("amount"), event.get("currency")
        if amount is not None and currency:
            from .providers.stripe_provider import stripe_amount

            expected = stripe_amount(purchase.fiat_amount, purchase.currency)
            if int(amount) != expected or currency != purchase.currency.lower():
                logger.error(
                    "payments: montant/devise incohérents pour l'achat %s (%s %s ≠ %s %s)",
                    purchase.id,
                    amount,
                    currency,
                    expected,
                    purchase.currency,
                )
                return fail_purchase(purchase)
        if event.get("payment_ref"):
            Purchase.objects.filter(pk=purchase.pk).update(
                provider_payment_ref=event["payment_ref"]
            )
        return confirm_purchase(purchase)
    if kind in ("refunded", "disputed") and event.get("payment_ref"):
        purchase = Purchase.objects.filter(
            provider=provider_name, provider_payment_ref=event["payment_ref"]
        ).first()
        if purchase is None:
            return None
        return reverse_purchase(purchase, disputed=kind == "disputed")
    return None


# --- Tips -----------------------------------------------------------------------


def send_tip(
    from_user,
    channel_slug: str,
    aura_amount: int,
    message: str = "",
    idempotency_key: str | None = None,
) -> Tip:
    """Tip d'un viewer à un streamer approuvé : 30 % plateforme / 70 % créateur."""
    from channels_app.models import Channel

    aura_amount = int(aura_amount)
    if aura_amount < tip_min_aura():
        raise PaymentError(f"Le tip minimum est de {tip_min_aura()} Aura.")
    if idempotency_key:
        existing = Tip.objects.filter(from_user=from_user, idempotency_key=idempotency_key).first()
        if existing is not None:
            return existing
    channel = Channel.objects.select_related("user").filter(slug=channel_slug.lower()).first()
    if channel is None:
        raise PaymentError("Chaîne introuvable.")
    if channel.user_id == from_user.id:
        raise PaymentError("Tu ne peux pas te tipper toi-même.")
    if not channel.is_provisioned:
        raise PaymentError("Cette chaîne ne peut pas encore recevoir de tips.")

    try:
        with transaction.atomic():
            wallets = _lock_wallets(from_user, channel.user)
            sender, creator_wallet = wallets[from_user.pk], wallets[channel.user_id]
            if sender.aura_balance < aura_amount:
                raise InsufficientBalanceError("Solde Aura insuffisant.")
            creator_share, platform_fee = split(aura_amount, FeeRule.Product.TIP)
            tip = Tip.objects.create(
                from_user=from_user,
                to_channel=channel,
                aura_amount=aura_amount,
                creator_share=creator_share,
                platform_fee=platform_fee,
                message=message[:200],
                idempotency_key=idempotency_key or None,
            )
            _apply(
                sender,
                -aura_amount,
                LedgerEntry.Kind.TIP_SENT,
                f"channel:{channel.slug}",
                related=tip,
            )
            _apply(
                creator_wallet,
                creator_share,
                LedgerEntry.Kind.TIP_RECEIVED,
                f"from:{from_user.username}",
                related=tip,
            )
            _record_fee(PlatformRevenue.Source.TIP, platform_fee, user=from_user, related=tip)
            transaction.on_commit(lambda: _after_tip(tip, from_user, channel))
    except IntegrityError:
        # Même clé d'idempotence envoyée en parallèle : renvoie le tip déjà créé.
        existing = Tip.objects.filter(from_user=from_user, idempotency_key=idempotency_key).first()
        if existing is None:
            raise
        return existing
    return tip


def _after_tip(tip: Tip, from_user, channel) -> None:
    """Notification, succès, anti-triche — APRÈS commit (best-effort)."""
    try:
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
    except Exception:  # noqa: BLE001 — n'annule jamais un tip déjà encaissé
        logger.exception("after_tip side effects failed for tip %s", tip.pk)

    with contextlib.suppress(Exception):
        from safety.anticheat import evaluate_self_deal, evaluate_tip

        evaluate_tip(from_user, channel)
        evaluate_self_deal(from_user, channel)


# --- Abonnements ----------------------------------------------------------------


@transaction.atomic
def charge_subscription(payer, creator, amount: int, related=None) -> tuple[int, int]:
    """Débite l'abonné en Aura et crédite le créateur (split). Retourne (part, commission)."""
    amount = int(amount)
    if amount <= 0:
        raise PaymentError("Montant invalide.")
    wallets = _lock_wallets(payer, creator)
    wallet, creator_wallet = wallets[payer.pk], wallets[creator.pk]
    if wallet.aura_balance < amount:
        raise InsufficientBalanceError("Solde Aura insuffisant.")
    creator_share, platform_fee = split(amount, FeeRule.Product.SUBSCRIPTION)
    _apply(wallet, -amount, LedgerEntry.Kind.SUB_PAID, f"sub:{creator.username}", related=related)
    _apply(
        creator_wallet,
        creator_share,
        LedgerEntry.Kind.SUB_EARNED,
        f"sub-from:{payer.username}",
        related=related,
    )
    _record_fee(PlatformRevenue.Source.SUBSCRIPTION, platform_fee, user=payer, related=related)
    return creator_share, platform_fee


# --- Retraits -------------------------------------------------------------------

WITHDRAWAL_OTP_TTL_MIN = 10
PHONE_RE = re.compile(r"^\+?[0-9]{8,15}$")


def is_eligible_streamer(user) -> bool:
    """Seuls les streamers approuvés (chaîne provisionnée) peuvent retirer."""
    return _is_streamer(user)


def withdrawable_balance(user) -> int:
    """Aura retirable = Aura GAGNÉE (tips + abonnements reçus, hors achats, bonus
    et parrainage), diminuée des retraits non échoués, plafonnée par le solde.
    Zéro si les retraits sont gelés.
    """
    wallet = get_wallet(user)
    if wallet.payout_hold:
        return 0
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
    return max(0, min(available, wallet.aura_balance))


def withdrawal_quote(aura_amount: int) -> dict:
    """Devis de retrait — exactement le calcul utilisé à la création du payout."""
    aura_amount = max(0, int(aura_amount))
    fee_aura = _pct_of(aura_amount, decimal.Decimal(str(withdrawal_fee_pct())) * 100)
    net_aura = aura_amount - fee_aura
    return {
        "aura": aura_amount,
        "fee_pct": float(round(withdrawal_fee_pct() * 100, 2)),
        "fee_aura": fee_aura,
        "net_aura": net_aura,
        "net_fiat": str(_fiat_for(net_aura)),
        "currency": "XOF",
        "min_aura": withdrawal_min_aura(),
    }


def _validate_destination(provider: str, phone: str) -> tuple[str, str]:
    provider = (provider or "").strip()
    phone = re.sub(r"[\s.-]", "", phone or "")
    if provider not in PayoutDestination.values:
        raise PaymentError("Choisis Wave ou Orange Money pour recevoir ton retrait.")
    if not PHONE_RE.match(phone):
        raise PaymentError("Numéro de téléphone invalide.")
    return provider, phone


def _check_withdrawal(user, aura_amount: int) -> None:
    if not is_eligible_streamer(user):
        raise PaymentError("Seuls les streamers approuvés peuvent demander un retrait.")
    if get_wallet(user).payout_hold:
        raise PaymentError("Tes retraits sont temporairement suspendus. Contacte le support.")
    if aura_amount < withdrawal_min_aura():
        raise PaymentError(f"Le retrait minimum est de {withdrawal_min_aura()} Aura.")
    if aura_amount > withdrawable_balance(user):
        raise InsufficientBalanceError("Montant supérieur à ton solde retirable.")


def start_withdrawal(user, aura_amount: int, destination_provider: str, destination_phone: str):
    """Valide la demande et émet un code OTP (envoyé par email uniquement)."""
    import secrets

    from .models import PayoutOtp

    aura_amount = int(aura_amount)
    provider, phone = _validate_destination(destination_provider, destination_phone)
    _check_withdrawal(user, aura_amount)
    # Invalide les OTP en attente précédents.
    PayoutOtp.objects.filter(user=user, consumed=False).update(consumed=True)
    code = f"{secrets.randbelow(1_000_000):06d}"
    otp = PayoutOtp.objects.create(
        user=user,
        aura_amount=aura_amount,
        destination_provider=provider,
        destination_phone=phone,
        code_hash=_hash_otp(code),
        expires_at=timezone.now() + timezone.timedelta(minutes=WITHDRAWAL_OTP_TTL_MIN),
    )
    _send_withdrawal_otp(user, code)
    return otp


@transaction.atomic
def confirm_withdrawal(user, code: str) -> Payout:
    """Vérifie l'OTP (ligne verrouillée → usage unique) puis crée le retrait.

    Toutes les vérifications sont refaites sous verrou du wallet : deux
    confirmations parallèles ne peuvent pas créer deux retraits.
    """
    from .models import PayoutOtp

    otp = (
        PayoutOtp.objects.select_for_update()
        .filter(user=user, consumed=False, expires_at__gte=timezone.now())
        .order_by("-created_at")
        .first()
    )
    if otp is None or not _verify_otp(otp.code_hash, code):
        raise PaymentError("Code de vérification invalide ou expiré.")
    otp.consumed = True
    otp.save(update_fields=["consumed"])
    return create_payout(
        user,
        otp.aura_amount,
        destination_provider=otp.destination_provider,
        destination_phone=otp.destination_phone,
    )


@transaction.atomic
def create_payout(
    user,
    aura_amount: int,
    destination_provider: str = "",
    destination_phone: str = "",
    idempotency_key: str | None = None,
) -> Payout:
    """Crée le retrait : débite l'Aura brute (mise en réserve), calcule le net.

    Usage interne uniquement (après OTP) : toutes les règles de retrait sont
    revérifiées sous verrou du wallet.
    """
    aura_amount = int(aura_amount)
    if idempotency_key:
        existing = Payout.objects.filter(user=user, idempotency_key=idempotency_key).first()
        if existing is not None:
            return existing
    wallet = _lock_wallets(user)[user.pk]
    _check_withdrawal(user, aura_amount)
    quote = withdrawal_quote(aura_amount)
    payout = Payout.objects.create(
        user=user,
        aura_amount=aura_amount,
        fee_aura=quote["fee_aura"],
        fiat_amount=decimal.Decimal(quote["net_fiat"]),
        destination_provider=destination_provider,
        destination_phone=destination_phone,
        idempotency_key=idempotency_key or None,
    )
    _apply(wallet, -aura_amount, LedgerEntry.Kind.PAYOUT, "payout", related=payout)
    from audit.services import record

    record(user, "payout.request", target=payout, meta={"aura": aura_amount, **quote})
    return payout


def _hash_otp(code: str) -> str:
    import hashlib

    return hashlib.sha256(code.encode()).hexdigest()


def _verify_otp(code_hash: str, code: str) -> bool:
    import hmac as _hmac

    return _hmac.compare_digest(code_hash, _hash_otp((code or "").strip()))


def _send_withdrawal_otp(user, code: str) -> None:
    """Envoie le code par EMAIL uniquement (second canal, hors session web)."""
    ttl = WITHDRAWAL_OTP_TTL_MIN
    with contextlib.suppress(Exception):
        from django.core.mail import send_mail

        send_mail(
            subject="Code de confirmation de retrait — Neyla TV",
            message=(
                f"Ton code de confirmation de retrait est : {code}\n"
                f"Valable {ttl} minutes. Si tu n'as pas demandé de retrait, "
                "change ton mot de passe et contacte le support."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )


@transaction.atomic
def resolve_payout(admin, payout: Payout, action: str) -> Payout:
    """Action admin sur un retrait.

    - `processing` : versement mobile money lancé ;
    - `paid` : versé (les frais de traitement deviennent un revenu plateforme) ;
    - `fail` : rejeté → l'Aura brute est recréditée (écriture `payout_reversal`).
    """
    if action not in ("processing", "paid", "fail"):
        raise PaymentError("Action invalide.")
    locked = Payout.objects.select_for_update().get(pk=payout.pk)
    if locked.status not in (Payout.Status.REQUESTED, Payout.Status.PROCESSING):
        raise PaymentError("Ce retrait a déjà été traité.")
    if action == "processing":
        if locked.status != Payout.Status.REQUESTED:
            raise PaymentError("Ce retrait est déjà en cours de versement.")
        locked.status = Payout.Status.PROCESSING
        locked.save(update_fields=["status"])
    elif action == "paid":
        locked.status = Payout.Status.PAID
        locked.resolved_at = timezone.now()
        locked.save(update_fields=["status", "resolved_at"])
        _record_fee(
            PlatformRevenue.Source.WITHDRAWAL, locked.fee_aura, user=locked.user, related=locked
        )
    else:
        wallet = _lock_wallets(locked.user)[locked.user_id]
        _apply(
            wallet,
            locked.aura_amount,
            LedgerEntry.Kind.PAYOUT_REVERSAL,
            "payout-refund",
            related=locked,
        )
        locked.status = Payout.Status.FAILED
        locked.resolved_at = timezone.now()
        locked.save(update_fields=["status", "resolved_at"])
    from audit.services import record

    record(admin, f"payout.{action}", target=locked, meta={"aura": locked.aura_amount})
    payout.refresh_from_db()
    return locked


# --- Réconciliation -------------------------------------------------------------


def wallet_drift() -> list[dict]:
    """Wallets dont le solde diffère de la somme du ledger (doit être vide)."""
    sums = dict(
        LedgerEntry.objects.values("wallet_id")
        .annotate(s=Sum("amount"))
        .values_list("wallet_id", "s")
    )
    drift = []
    for wallet in Wallet.objects.select_related("user").iterator():
        expected = int(sums.get(wallet.id) or 0)
        if expected != wallet.aura_balance:
            drift.append(
                {
                    "wallet": wallet.id,
                    "user": wallet.user.username,
                    "balance": wallet.aura_balance,
                    "ledger_sum": expected,
                    "delta": wallet.aura_balance - expected,
                }
            )
    return drift


# --- Vue admin ------------------------------------------------------------------


def list_transactions(type_filter: str = "", query: str = "", days: int = 0) -> list[dict]:
    """Flux unifié Purchase/Tip/Subscription/Payout (récent d'abord) pour l'admin."""
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
                    "aura": s.price_paid or (s.tier.price_aura if s.tier else 0),
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
            dest = p.get_destination_provider_display() if p.destination_provider else ""
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
                    "detail": f"{p.fiat_amount} {p.currency} {dest} {p.destination_phone}".strip(),
                }
            )

    rows.sort(key=lambda r: r["created_at"], reverse=True)
    return rows
