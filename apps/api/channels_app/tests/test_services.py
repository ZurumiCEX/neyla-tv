"""Tests des services métier (provision, rotate, mark_live/offline)."""

from __future__ import annotations

import pytest

from accounts.factories import UserFactory
from channels_app.models import Channel, StreamSession
from channels_app.services import (
    mark_live,
    mark_offline,
    provision_channel,
    record_session_peak,
    rotate_stream_key,
)

pytestmark = pytest.mark.django_db


def test_new_user_channel_is_not_provisioned():
    """L'inscription crée une chaîne mais NE provisionne PAS (gating streamer)."""
    user = UserFactory()
    channel = Channel.objects.get(user=user)
    assert channel.live_input_uid == ""
    assert not channel.is_provisioned


def test_provision_is_idempotent():
    user = UserFactory()
    channel = Channel.objects.get(user=user)
    provision_channel(channel)
    first_uid = channel.live_input_uid
    assert first_uid  # provisionné
    provision_channel(channel)
    assert channel.live_input_uid == first_uid


def test_rotate_key_changes_credentials():
    user = UserFactory()
    channel = Channel.objects.get(user=user)
    provision_channel(channel)
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


def test_mark_live_opens_session_offline_closes_it():
    channel = Channel.objects.get(user=UserFactory())
    channel.title = "Speedrun"
    channel.save(update_fields=["title"])
    mark_live(channel)
    session = StreamSession.objects.get(channel=channel)
    assert session.ended_at is None
    assert session.title_snapshot == "Speedrun"
    mark_offline(channel)
    session.refresh_from_db()
    assert session.ended_at is not None
    assert session.duration_seconds is not None


def test_record_session_peak_only_increases():
    channel = Channel.objects.get(user=UserFactory())
    mark_live(channel)
    record_session_peak(channel.id, 5)
    record_session_peak(channel.id, 3)  # plus petit → ignoré
    session = StreamSession.objects.get(channel=channel)
    assert session.peak_viewers == 5
