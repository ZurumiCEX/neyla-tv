"""Tests Charity Day : modèle, service, endpoints, transparence."""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.factories import UserFactory
from charity import services
from charity.models import Charity, CharityDonation, CharityEvent
from payments import services as pay
from payments.models import LedgerEntry

pytestmark = pytest.mark.django_db


def _ev(slug="aout-2026", floor=10, open_now=True):
    now = timezone.now()
    starts = now - timezone.timedelta(hours=1) if open_now else now + timezone.timedelta(days=2)
    ends = starts + timezone.timedelta(days=1)
    e = CharityEvent.objects.create(
        slug=slug, title=f"Charity {slug}", starts_at=starts, ends_at=ends, floor_aura=floor
    )
    c = Charity.objects.create(slug=f"{slug}-c", name="Cause A", country="SN")
    e.beneficiaries.add(c)
    return e, c


def _fan_with_aura(amount: int = 1000):
    """Crée un user avec `amount` Aura crédités."""
    u = UserFactory()
    pay.create_purchase(u, amount)
    return u


def test_donate_debits_ledger_and_updates_cache():
    e, c = _ev(floor=50)
    fan = _fan_with_aura(1000)
    d = services.donate(fan, e.slug, c.slug, 200, "go go")
    assert d.aura_amount == 200
    assert d.donor_id == fan.id
    # Wallet débité.
    assert pay.get_wallet(fan).aura_balance == 800
    # Ledger entry CHARITY_DONATION écrite (-200).
    le = LedgerEntry.objects.filter(
        wallet__user=fan, kind=LedgerEntry.Kind.CHARITY_DONATION
    ).first()
    assert le is not None and le.amount == -200
    # Cache total mis à jour.
    e.refresh_from_db()
    assert e.total_aura_cached == 200


def test_donate_refuses_below_floor():
    e, c = _ev(floor=50)
    fan = _fan_with_aura()
    with pytest.raises(services.CharityError):
        services.donate(fan, e.slug, c.slug, 10)


def test_donate_refuses_when_event_closed():
    e, c = _ev(floor=10, open_now=False)
    fan = _fan_with_aura()
    with pytest.raises(services.CharityError):
        services.donate(fan, e.slug, c.slug, 50)


def test_donate_refuses_when_charity_not_beneficiary():
    e, c = _ev()
    other = Charity.objects.create(slug="other", name="Other")
    fan = _fan_with_aura()
    with pytest.raises(services.CharityError):
        services.donate(fan, e.slug, other.slug, 50)


def test_donate_refuses_insufficient_balance():
    e, c = _ev(floor=10)
    fan = UserFactory()  # wallet vide
    with pytest.raises(pay.InsufficientBalanceError):
        services.donate(fan, e.slug, c.slug, 50)


def test_aggregates_leaderboard_anonymizes():
    e, c = _ev(floor=10)
    a, b = _fan_with_aura(500), _fan_with_aura(500)
    services.donate(a, e.slug, c.slug, 100)
    services.donate(b, e.slug, c.slug, 200, is_anonymous=True)
    agg = services.aggregates(e)
    assert agg["total"] == 300
    assert agg["donor_count"] == 2
    # Top 1 (200) est anonyme.
    assert agg["top_donors"][0]["display_name"] == "Anonyme"
    assert agg["top_donors"][0]["username"] == "—"


def test_streamer_compliance_tracks_floor():
    from channels_app.models import Channel
    from channels_app.services import provision_channel

    e, c = _ev(floor=100)
    streamer = _fan_with_aura(500)
    provision_channel(Channel.objects.get(user=streamer))
    assert services.streamer_compliance(streamer, e)["has_donated"] is False
    services.donate(streamer, e.slug, c.slug, 100)
    state = services.streamer_compliance(streamer, e)
    assert state["has_donated"] is True
    assert state["total_donated"] == 100
    assert state["floor"] == 100


def test_endpoint_current_event_public(api_client):
    e, c = _ev()
    fan = _fan_with_aura()
    services.donate(fan, e.slug, c.slug, 50)
    resp = api_client.get(reverse("charity-current"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["event"]["slug"] == e.slug
    assert body["total"] == 50
    assert len(body["by_charity"]) == 1


def test_endpoint_donate_creates_donation(auth_client_factory):
    e, c = _ev(floor=10)
    fan = _fan_with_aura()
    client = auth_client_factory(fan)
    resp = client.post(
        reverse("charity-donate"),
        {"event_slug": e.slug, "charity_slug": c.slug, "aura_amount": 100},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    assert CharityDonation.objects.count() == 1


def test_endpoint_donate_requires_auth(api_client):
    e, c = _ev()
    resp = api_client.post(
        reverse("charity-donate"),
        {"event_slug": e.slug, "charity_slug": c.slug, "aura_amount": 50},
        format="json",
    )
    assert resp.status_code == 401


def test_endpoint_list_events_public(api_client):
    _ev("a")
    _ev("b", open_now=False)
    resp = api_client.get(reverse("charity-events"))
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 2


# --- PlatformEvent (calendrier) ---


def test_charity_event_mirrors_into_platform_event():
    from charity.models import PlatformEvent

    e, _ = _ev("july-2026")
    pe = PlatformEvent.objects.filter(slug=f"charity-{e.slug}").first()
    assert pe is not None
    assert pe.kind == PlatformEvent.Kind.CHARITY
    assert pe.link_url == "/charity"
    assert pe.is_published is True
    # Update propagates.
    e.is_published = False
    e.save()
    pe.refresh_from_db()
    assert pe.is_published is False
    # Delete removes mirror.
    e.delete()
    assert not PlatformEvent.objects.filter(slug=f"charity-{e.slug}").exists()


def test_upcoming_platform_events_endpoint(api_client):
    from charity.models import PlatformEvent

    now = timezone.now()
    PlatformEvent.objects.create(
        slug="t1",
        title="T1",
        kind=PlatformEvent.Kind.TOURNAMENT,
        starts_at=now + timezone.timedelta(days=1),
        ends_at=now + timezone.timedelta(days=2),
    )
    PlatformEvent.objects.create(
        slug="past",
        title="P",
        kind=PlatformEvent.Kind.ANNOUNCEMENT,
        starts_at=now - timezone.timedelta(days=10),
        ends_at=now - timezone.timedelta(days=9),
    )
    resp = api_client.get(reverse("platform-events-upcoming"))
    slugs = [e["slug"] for e in resp.json()["results"]]
    assert "t1" in slugs and "past" not in slugs
