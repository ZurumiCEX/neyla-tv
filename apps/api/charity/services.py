"""Logique métier Charity : don atomique au ledger, agrégats, conformité."""

from __future__ import annotations

from django.db import transaction
from django.db.models import Count, F, Sum
from django.utils import timezone

from .models import Charity, CharityDonation, CharityEvent


class CharityError(Exception):
    """Erreur métier (validation, état)."""


def current_event() -> CharityEvent | None:
    """Événement publié en cours (si plusieurs, le plus récent)."""
    now = timezone.now()
    return (
        CharityEvent.objects.filter(is_published=True, starts_at__lte=now, ends_at__gte=now)
        .order_by("-starts_at")
        .first()
    )


def next_event() -> CharityEvent | None:
    """Prochain événement à venir."""
    now = timezone.now()
    return (
        CharityEvent.objects.filter(is_published=True, starts_at__gt=now)
        .order_by("starts_at")
        .first()
    )


@transaction.atomic
def donate(
    user,
    event_slug: str,
    charity_slug: str,
    aura_amount: int,
    message: str = "",
    is_anonymous: bool = False,
) -> CharityDonation:
    """Don atomique : débit ledger + création CharityDonation + maj cache total.

    Refuse : événement non publié / fermé, montant < floor, association inactive.
    """
    from payments.models import LedgerEntry
    from payments.services import _apply, _lock_wallets

    event = CharityEvent.objects.select_for_update().filter(slug=event_slug.lower()).first()
    if event is None:
        raise CharityError("Événement introuvable.")
    if not event.is_open:
        raise CharityError("Cet événement n'accepte plus de dons.")

    charity = Charity.objects.filter(slug=charity_slug.lower(), is_active=True).first()
    if charity is None:
        raise CharityError("Association introuvable.")
    if charity not in event.beneficiaries.all():
        raise CharityError("Cette association n'est pas bénéficiaire de l'événement.")

    aura_amount = int(aura_amount)
    if aura_amount < event.floor_aura:
        raise CharityError(f"Le don minimum pour cet événement est de {event.floor_aura} Aura.")

    # Wallet verrouillé : un don concurrent d'un tip/retrait ne peut plus
    # écraser le débit de l'autre (lost update).
    wallet = _lock_wallets(user)[user.pk]
    _apply(
        wallet,
        -aura_amount,
        LedgerEntry.Kind.CHARITY_DONATION,
        reference=f"charity:{event.slug}:{charity.slug}",
        metadata={"event": event.slug, "charity": charity.slug, "anonymous": is_anonymous},
    )

    donation = CharityDonation.objects.create(
        event=event,
        donor=user,
        charity=charity,
        aura_amount=aura_amount,
        message=message[:140],
        is_anonymous=is_anonymous,
    )

    # Mise à jour atomique du total caché (évite un recompte à chaque lecture).
    CharityEvent.objects.filter(pk=event.pk).update(
        total_aura_cached=F("total_aura_cached") + aura_amount
    )

    def _after_donation() -> None:
        from gamification.services import check_and_award

        check_and_award(user, "charity")
        check_and_award(user, "spend")

    transaction.on_commit(_after_donation)
    return donation


def aggregates(event: CharityEvent, top: int = 10) -> dict:
    """Agrégats pour l'affichage public d'un événement."""
    qs = event.donations.all()
    summary = qs.aggregate(total=Sum("aura_amount"), donor_count=Count("donor", distinct=True))
    by_charity = list(
        qs.values("charity__slug", "charity__name", "charity__logo_url")
        .annotate(total=Sum("aura_amount"), count=Count("id"))
        .order_by("-total")
    )
    # Top donateurs (anonymes affichés sans pseudo).
    leaderboard = []
    for d in qs.select_related("donor").order_by("-aura_amount", "created_at")[:top]:
        leaderboard.append(
            {
                "username": "—" if d.is_anonymous else d.donor.username,
                "display_name": (
                    "Anonyme" if d.is_anonymous else (d.donor.display_name or d.donor.username)
                ),
                "is_streamer": _is_streamer(d.donor) and not d.is_anonymous,
                "aura_amount": d.aura_amount,
                "created_at": d.created_at,
            }
        )
    disbursed = event.disbursements.aggregate(aura=Sum("aura_amount"), xof=Sum("fiat_amount_xof"))
    total = int(summary["total"] or 0)
    disbursed_aura = int(disbursed["aura"] or 0)
    return {
        "total": total,
        "donor_count": int(summary["donor_count"] or 0),
        "by_charity": by_charity,
        "top_donors": leaderboard,
        "disbursed_aura": disbursed_aura,
        "disbursed_xof": int(disbursed["xof"] or 0),
        "pending_aura": max(0, total - disbursed_aura),
        "disbursements": [
            {
                "charity": d.charity.name,
                "fiat_amount_xof": d.fiat_amount_xof,
                "reference": d.reference,
                "paid_at": d.paid_at,
                "proof_url": d.proof_url,
            }
            for d in event.disbursements.select_related("charity")[:20]
        ],
    }


def _is_streamer(user) -> bool:
    """Marque visuelle dans le leaderboard (badge streamer)."""
    from channels_app.utils import is_streamer

    return is_streamer(user)


def streamer_compliance(user, event: CharityEvent) -> dict:
    """Conformité d'un streamer à l'obligation Charity Day pour un événement.

    Retourne `{has_donated, total_donated, floor}` (lecture seule, pour UI).
    """
    total = (
        CharityDonation.objects.filter(event=event, donor=user).aggregate(s=Sum("aura_amount"))["s"]
        or 0
    )
    return {
        "has_donated": int(total) >= event.floor_aura,
        "total_donated": int(total),
        "floor": event.floor_aura,
    }
