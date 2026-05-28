"""Tests abonnements : palier, souscription Aura (split), solde, statut, annulation."""

from __future__ import annotations

import pytest

from accounts.factories import UserFactory
from channels_app.models import Channel
from payments import services as pay
from subscriptions import services
from subscriptions.models import Subscription

pytestmark = pytest.mark.django_db


def _streamer():
    user = UserFactory()
    channel = Channel.objects.get(user=user)
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
    channel = Channel.objects.get(user=UserFactory())
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
    services.cancel(fan, channel.slug)
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
