"""Signal post_save sur User : crée et provisionne une Channel."""

from __future__ import annotations

import pytest

from accounts.factories import UserFactory
from channels_app.models import Channel

pytestmark = pytest.mark.django_db


def test_channel_created_on_user_signup():
    user = UserFactory(username="streamer1")
    channel = Channel.objects.get(user=user)
    assert channel.slug == "streamer1"


def test_channel_not_provisioned_at_signup():
    """Le provisionnement Cloudflare est déclenché à l'approbation streamer,
    pas à l'inscription : une Channel fraîche est créée NON provisionnée."""
    user = UserFactory(username="streamer2")
    channel = Channel.objects.get(user=user)
    assert not channel.is_provisioned
    assert channel.live_input_uid == ""
    assert channel.rtmps_url == ""
    assert channel.rtmps_key == ""
    assert channel.hls_playback_url == ""


def test_no_duplicate_channel_on_user_update():
    user = UserFactory(username="streamer3")
    before = Channel.objects.filter(user=user).count()
    user.display_name = "Streamer Three"
    user.save()
    after = Channel.objects.filter(user=user).count()
    assert before == after == 1
