"""Tests cadeau d'abonnement (gift_subscription + endpoints)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.models import Channel
from payments import services as pay
from subscriptions import services
from subscriptions.models import Subscription

pytestmark = pytest.mark.django_db


def _streamer():
    channel = Channel.objects.get(user=UserFactory())
    services.set_tier(channel, price_aura=100, perks=["Badge"])
    return channel


def test_gift_subscription_debits_gifter_and_subscribes_recipient():
    channel = _streamer()
    gifter = UserFactory()
    recipient = UserFactory()
    pay.create_purchase(gifter, 500)

    sub = services.gift_subscription(gifter, channel.slug, recipient.username)
    assert sub.subscriber_id == recipient.id
    assert sub.gifted_by_id == gifter.id
    assert sub.status == Subscription.Status.ACTIVE
    # L'offreur a été débité de 100 Aura.
    assert pay.get_wallet(gifter).aura_balance == 400


def test_gift_subscription_refuses_self_gift():
    channel = _streamer()
    gifter = UserFactory()
    pay.create_purchase(gifter, 500)
    with pytest.raises(services.SubscriptionError):
        services.gift_subscription(gifter, channel.slug, gifter.username)


def test_gift_subscription_refuses_offering_to_creator():
    channel = _streamer()
    gifter = UserFactory()
    pay.create_purchase(gifter, 500)
    with pytest.raises(services.SubscriptionError):
        services.gift_subscription(gifter, channel.slug, channel.user.username)


def test_gift_subscription_refuses_unknown_recipient():
    channel = _streamer()
    gifter = UserFactory()
    pay.create_purchase(gifter, 500)
    with pytest.raises(services.SubscriptionError):
        services.gift_subscription(gifter, channel.slug, "ghost")


def test_gift_subscription_refuses_insufficient_balance():
    from payments.services import InsufficientBalanceError

    channel = _streamer()
    gifter = UserFactory()
    recipient = UserFactory()
    with pytest.raises(InsufficientBalanceError):
        services.gift_subscription(gifter, channel.slug, recipient.username)


def test_gift_endpoint_creates_subscription(auth_client_factory):
    channel = _streamer()
    gifter = UserFactory()
    recipient = UserFactory()
    pay.create_purchase(gifter, 500)
    client = auth_client_factory(gifter)
    resp = client.post(
        reverse("subscription-gift"),
        {"channel_slug": channel.slug, "recipient": recipient.username},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    assert resp.json()["recipient"] == recipient.username


def test_my_gifts_endpoint_lists_gifted_subscriptions(auth_client_factory):
    channel = _streamer()
    gifter = UserFactory()
    recipient = UserFactory()
    pay.create_purchase(gifter, 500)
    services.gift_subscription(gifter, channel.slug, recipient.username)
    client = auth_client_factory(gifter)
    resp = client.get(reverse("subscription-mine-gifts"))
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["recipient"]["username"] == recipient.username
    assert results[0]["channel"]["slug"] == channel.slug


def test_gifts_endpoint_requires_auth(api_client):
    assert api_client.get(reverse("subscription-mine-gifts")).status_code == 401
