"""Tests des services métier (provision, rotate, mark_live/offline)."""

from __future__ import annotations

import pytest

from accounts.factories import UserFactory
from channels_app.models import Channel
from channels_app.services import (
    mark_live,
    mark_offline,
    provision_channel,
    rotate_stream_key,
)

pytestmark = pytest.mark.django_db


def test_provision_is_idempotent():
    user = UserFactory()
    channel = Channel.objects.get(user=user)
    first_uid = channel.live_input_uid
    provision_channel(channel)
    assert channel.live_input_uid == first_uid


def test_rotate_key_changes_credentials():
    user = UserFactory()
    channel = Channel.objects.get(user=user)
    old_uid = channel.live_input_uid
    old_key = channel.rtmps_key
    rotate_stream_key(channel)
    channel.refresh_from_db()
    assert channel.live_input_uid != old_uid
    assert channel.rtmps_key != old_key


def test_mark_live_toggles_and_sets_timestamp():
    user = UserFactory()
    channel = Channel.objects.get(user=user)
    assert mark_live(channel) is True
    assert channel.is_live
    assert channel.last_live_started_at is not None
    # 2e appel : aucun changement.
    assert mark_live(channel) is False


def test_mark_offline_idempotent():
    user = UserFactory()
    channel = Channel.objects.get(user=user)
    assert mark_offline(channel) is False
    mark_live(channel)
    assert mark_offline(channel) is True
    assert not channel.is_live
