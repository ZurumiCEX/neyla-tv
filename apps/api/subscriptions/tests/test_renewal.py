"""Tests renouvellement/expiration des abonnements (process_due_subscriptions)."""

from __future__ import annotations

import pytest
from django.utils import timezone

from accounts.factories import UserFactory
from channels_app.models import Channel
from payments import services as pay
from subscriptions import services
from subscriptions.models import Subscription

pytestmark = pytest.mark.django_db


def _streamer(price=100):
    channel = Channel.objects.get(user=UserFactory())
    services.set_tier(channel, price_aura=price, perks=[])
    return channel


def _make_due(sub):
    Subscription.objects.filter(id=sub.id).update(
        current_period_end=timezone.now() - timezone.timedelta(days=1)
    )


def test_renew_when_balance_sufficient():
    channel = _streamer(price=100)
    fan = UserFactory()
    pay.create_purchase(fan, 500)
    sub = services.subscribe(fan, channel.slug)  # débite 100 -> 400
    _make_due(sub)

    result = services.process_due_subscriptions()

    assert result == {"renewed": 1, "expired": 0}
    sub.refresh_from_db()
    assert sub.status == Subscription.Status.ACTIVE
    assert sub.current_period_end > timezone.now()
    assert pay.get_wallet(fan).aura_balance == 300  # 400 - 100 (renouvellement)


def test_expire_when_balance_insufficient():
    channel = _streamer(price=100)
    fan = UserFactory()
    pay.create_purchase(fan, 100)
    sub = services.subscribe(fan, channel.slug)  # solde 0 après débit
    _make_due(sub)

    result = services.process_due_subscriptions()

    assert result == {"renewed": 0, "expired": 1}
    sub.refresh_from_db()
    assert sub.status == Subscription.Status.EXPIRED


def test_expire_when_tier_inactive():
    channel = _streamer(price=100)
    fan = UserFactory()
    pay.create_purchase(fan, 500)
    sub = services.subscribe(fan, channel.slug)
    services.set_tier(channel, price_aura=100, perks=[], is_active=False)
    _make_due(sub)

    result = services.process_due_subscriptions()

    assert result == {"renewed": 0, "expired": 1}
    sub.refresh_from_db()
    assert sub.status == Subscription.Status.EXPIRED


def test_not_due_subscription_untouched():
    channel = _streamer(price=100)
    fan = UserFactory()
    pay.create_purchase(fan, 500)
    sub = services.subscribe(fan, channel.slug)  # période future

    result = services.process_due_subscriptions()

    assert result == {"renewed": 0, "expired": 0}
    sub.refresh_from_db()
    assert sub.status == Subscription.Status.ACTIVE
    assert pay.get_wallet(fan).aura_balance == 400
