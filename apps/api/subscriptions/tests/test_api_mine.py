"""Tests endpoint « mes abonnements » (page Suivis)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.models import Channel
from payments import services as pay
from subscriptions import services

pytestmark = pytest.mark.django_db


def _streamer():
    channel = Channel.objects.get(user=UserFactory())
    services.set_tier(channel, price_aura=100, perks=["Badge"])
    return channel


def test_my_subscriptions_requires_auth(api_client):
    assert api_client.get(reverse("subscription-mine")).status_code == 401


def test_my_subscriptions_lists_active(auth_client_factory):
    channel = _streamer()
    fan = UserFactory()
    pay.create_purchase(fan, 500)
    services.subscribe(fan, channel.slug)
    client = auth_client_factory(fan)
    response = client.get(reverse("subscription-mine"))
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["channel"]["slug"] == channel.slug
    assert results[0]["tier_name"]
