"""Niveaux (Aura dépensée à vie), badges de don par chaîne et profil public."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from accounts.models import User
from channels_app.testing import provisioned_channel
from gamification.levels import gift_tier, level_for, level_progress
from gamification.models import ChannelSupport, UserAchievement
from payments import services as pay
from subscriptions import services as subs
from subscriptions.models import SubscriptionGift

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("spent", "level"),
    [
        (0, "rookie"),
        (9_999, "rookie"),
        (10_000, "beginner"),
        (50_000, "casual"),
        (100_000, "great"),
        (200_000, "lord"),
        (500_000, "mvp"),
        (999_999, "mvp"),
        (1_000_000, "goat"),
    ],
)
def test_level_thresholds(spent, level):
    assert level_for(spent) == level


def test_level_progress_and_gift_tiers():
    assert level_progress(30_000) == {
        "level": "beginner",
        "next_level": "casual",
        "next_at": 50_000,
        "progress": 50,
    }
    assert level_progress(2_000_000)["next_level"] is None
    assert [gift_tier(n) for n in (0, 1, 99, 100, 1_000, 5_000, 10_000)] == [
        None,
        "spark",
        "spark",
        "glow",
        "radiant",
        "nova",
        "supreme",
    ]


def _spent(user) -> int:
    return User.objects.get(pk=user.pk).lifetime_aura_spent


def test_tips_subs_and_gifts_count_as_spend_and_support(django_capture_on_commit_callbacks):
    channel = provisioned_channel(UserFactory())
    subs.set_tier(channel, price_aura=100, perks=[])
    fan, friend = UserFactory(), UserFactory()
    pay.create_purchase(fan, 5_000)
    assert _spent(fan) == 0  # un achat n'est pas une dépense

    with django_capture_on_commit_callbacks(execute=True):
        pay.send_tip(fan, channel.slug, 300, "GG")
        subs.subscribe(fan, channel.slug)
        subs.gift_subscription(fan, channel.slug, friend.username)

    assert _spent(fan) == 300 + 100 + 100
    support = ChannelSupport.objects.get(user=fan, channel=channel)
    assert support.total_aura == 300 + 100  # tip + abonnement offert (pas son propre abo)
    assert SubscriptionGift.objects.filter(gifter=fan, recipient=friend).count() == 1
    keys = set(UserAchievement.objects.filter(user=fan).values_list("achievement__key", flat=True))
    assert {"gift_spark", "gift_glow", "first_gift_sub"} <= keys
    assert "gift_radiant" not in keys


def test_level_achievement_awarded_when_threshold_reached(django_capture_on_commit_callbacks):
    channel = provisioned_channel(UserFactory())
    whale = UserFactory()
    pay.create_purchase(whale, 12_000)
    with django_capture_on_commit_callbacks(execute=True):
        pay.send_tip(whale, channel.slug, 10_000, "")
    assert UserAchievement.objects.filter(user=whale, achievement__key="level_beginner").exists()


def test_public_profile_hides_amounts_from_others(auth_client_factory, api_client):
    channel = provisioned_channel(UserFactory())
    fan = UserFactory()
    pay.create_purchase(fan, 2_000)
    pay.send_tip(fan, channel.slug, 1_500, "")

    public = api_client.get(reverse("public-profile", kwargs={"username": fan.username})).json()
    assert public["level"]["level"] == "rookie"
    assert "spent" not in public["level"]
    assert public["supported"][0]["slug"] == channel.slug
    assert public["supported"][0]["gift_tier"] == "radiant"
    assert "total_aura" not in public["supported"][0]
    assert public["is_owner"] is False

    own = (
        auth_client_factory(fan)
        .get(reverse("public-profile", kwargs={"username": fan.username}))
        .json()
    )
    assert own["is_owner"] is True
    assert own["level"]["spent"] == 1_500
    assert own["supported"][0]["total_aura"] == 1_500

    me = auth_client_factory(fan).get(reverse("my-level")).json()
    assert me["spent"] == 1_500 and me["next_level"] == "beginner"


def test_unknown_profile_is_404(api_client):
    assert (
        api_client.get(reverse("public-profile", kwargs={"username": "nobody"})).status_code == 404
    )
