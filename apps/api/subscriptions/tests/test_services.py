"""Tests abonnements : palier, souscription Aura (split), solde, statut, annulation."""

from __future__ import annotations

import pytest

from accounts.factories import UserFactory
from channels_app.testing import provisioned_channel
from payments import services as pay
from subscriptions import services
from subscriptions.models import Subscription

pytestmark = pytest.mark.django_db


def _streamer():
    user = UserFactory()
    channel = provisioned_channel(user)
    services.set_tier(channel, price_aura=100, perks=["Badge abonné", "Stickers"])
    return channel


def test_subscribe_debits_and_splits():
    channel = _streamer()
    fan = UserFactory()
    pay.create_purchase(fan, 500)
    sub = services.subscribe(fan, channel.slug)
    assert sub.status == Subscription.Status.ACTIVE
    assert sub.is_active
    assert pay.get_wallet(fan).aura_balance == 400
    assert pay.get_wallet(channel.user).aura_balance == 70  # 70% de 100


def test_subscribe_insufficient_balance():
    channel = _streamer()
    fan = UserFactory()
    with pytest.raises(pay.InsufficientBalanceError):
        services.subscribe(fan, channel.slug)


def test_cannot_subscribe_self():
    channel = _streamer()
    pay.create_purchase(channel.user, 500)
    with pytest.raises(services.SubscriptionError):
        services.subscribe(channel.user, channel.slug)


def test_no_tier_means_no_subscription():
    channel = provisioned_channel(UserFactory())
    fan = UserFactory()
    pay.create_purchase(fan, 500)
    with pytest.raises(services.SubscriptionError):
        services.subscribe(fan, channel.slug)


def test_subscriber_user_ids_lists_active_only():
    channel = _streamer()
    fan = UserFactory()
    pay.create_purchase(fan, 500)
    services.subscribe(fan, channel.slug)
    assert services.subscriber_user_ids(channel) == {fan.id}
    # Annuler coupe le renouvellement, pas l'accès déjà payé.
    services.cancel(fan, channel.slug)
    assert services.subscriber_user_ids(channel) == {fan.id}
    sub = Subscription.objects.get(subscriber=fan, channel=channel)
    assert sub.cancel_at_period_end and not sub.will_renew
    # Fin de période → expiré, plus listé.
    from django.utils import timezone

    Subscription.objects.filter(pk=sub.pk).update(current_period_end=timezone.now())
    services.process_due_subscriptions()
    assert services.subscriber_user_ids(channel) == set()


def test_subscribe_endpoint_and_status(auth_client_factory):
    from django.urls import reverse

    channel = _streamer()
    fan = UserFactory()
    pay.create_purchase(fan, 500)
    client = auth_client_factory(fan)
    resp = client.post(
        reverse("subscription-create"), {"channel_slug": channel.slug}, format="json"
    )
    assert resp.status_code == 201
    status_resp = client.get(reverse("subscription-status", kwargs={"slug": channel.slug}))
    assert status_resp.json()["subscribed"] is True


def test_set_tier_persists_badge_and_stickers():
    from accounts.factories import UserFactory
    from subscriptions import services

    user = UserFactory()
    channel = provisioned_channel(user)
    tier = services.set_tier(
        channel,
        price_aura=100,
        perks=["Badge abonné"],
        badge_url="https://example.com/badge.png",
        stickers_urls=["https://example.com/s1.png", "https://example.com/s2.png", ""],
    )
    assert tier.badge_url == "https://example.com/badge.png"
    assert tier.stickers_urls == [
        "https://example.com/s1.png",
        "https://example.com/s2.png",
    ]


def test_my_tier_put_accepts_badge_and_stickers(auth_client_factory):
    from django.urls import reverse

    from accounts.factories import UserFactory

    user = UserFactory()
    provisioned_channel(user)
    client = auth_client_factory(user)
    resp = client.put(
        reverse("streamer-tier"),
        {
            "price_aura": 200,
            "perks": ["Stickers exclusifs"],
            "badge_url": "https://example.com/b.png",
            "stickers_urls": ["https://example.com/x.png"],
            "is_active": True,
        },
        format="json",
    )
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert body["badge_url"] == "https://example.com/b.png"
    assert body["stickers_urls"] == ["https://example.com/x.png"]


def test_tier_put_forbidden_for_non_streamer(auth_client_factory):
    from django.urls import reverse

    resp = auth_client_factory(UserFactory()).put(
        reverse("streamer-tier"), {"price_aura": 100, "perks": []}, format="json"
    )
    assert resp.status_code == 403


def test_resubscribe_extends_instead_of_resetting():
    from django.utils import timezone

    channel = _streamer()
    fan = UserFactory()
    pay.create_purchase(fan, 500)
    first = services.subscribe(fan, channel.slug)
    end1 = first.current_period_end
    second = services.subscribe(fan, channel.slug)
    assert second.current_period_end - end1 >= timezone.timedelta(days=29)
    assert pay.get_wallet(fan).aura_balance == 300


def test_subscribe_idempotency_key_charges_once():
    channel = _streamer()
    fan = UserFactory()
    pay.create_purchase(fan, 500)
    a = services.subscribe(fan, channel.slug, idempotency_key="sub-1")
    b = services.subscribe(fan, channel.slug, idempotency_key="sub-1")
    assert a.pk == b.pk
    assert pay.get_wallet(fan).aura_balance == 400


def test_renewal_uses_locked_price_not_new_price():
    from django.utils import timezone

    channel = _streamer()  # 100 Aura
    fan = UserFactory()
    pay.create_purchase(fan, 1000)
    sub = services.subscribe(fan, channel.slug)
    services.set_tier(channel, price_aura=900, perks=[])  # hausse de prix
    Subscription.objects.filter(pk=sub.pk).update(current_period_end=timezone.now())
    services.process_due_subscriptions()
    assert pay.get_wallet(fan).aura_balance == 800  # 1000 - 100 - 100


def test_tier_price_capped(settings):
    settings.SUB_TIER_MAX_AURA = 1000
    channel = _streamer()
    with pytest.raises(services.SubscriptionError):
        services.set_tier(channel, price_aura=5000, perks=[])


def test_gifted_subscription_does_not_auto_renew():
    from django.utils import timezone

    channel = _streamer()
    gifter, recipient = UserFactory(), UserFactory()
    pay.create_purchase(gifter, 500)
    pay.create_purchase(recipient, 500)
    sub = services.gift_subscription(gifter, channel.slug, recipient.username)
    assert sub.auto_renew is False
    Subscription.objects.filter(pk=sub.pk).update(current_period_end=timezone.now())
    services.process_due_subscriptions()
    sub.refresh_from_db()
    assert sub.status == Subscription.Status.EXPIRED
    assert pay.get_wallet(recipient).aura_balance == 500  # jamais débité


def test_my_tier_get_returns_inactive_tier(auth_client_factory):
    channel = _streamer()
    services.set_tier(channel, price_aura=150, perks=["Badge"], is_active=False)
    from django.urls import reverse

    data = auth_client_factory(channel.user).get(reverse("streamer-tier")).json()
    assert data["is_active"] is False
    assert data["price_aura"] == 150
