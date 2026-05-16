"""Tests du modèle ChatBan."""

from __future__ import annotations

import pytest
from django.utils import timezone

from accounts.factories import UserFactory
from channels_app.factories import ChannelFactory
from chat.models import ChatBan

pytestmark = pytest.mark.django_db


def test_ban_permanent_is_active():
    ban = ChatBan.objects.create(channel=ChannelFactory(), user=UserFactory(), until=None)
    assert ban.is_active()


def test_ban_with_future_until_is_active():
    ban = ChatBan.objects.create(
        channel=ChannelFactory(),
        user=UserFactory(),
        until=timezone.now() + timezone.timedelta(minutes=10),
    )
    assert ban.is_active()


def test_ban_with_past_until_is_inactive():
    ban = ChatBan.objects.create(
        channel=ChannelFactory(),
        user=UserFactory(),
        until=timezone.now() - timezone.timedelta(minutes=1),
    )
    assert not ban.is_active()
