"""Tests du ChatConsumer via WebsocketCommunicator."""

from __future__ import annotations

import json

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.factories import UserFactory
from channels_app.models import Channel
from chat.models import ChatBan
from config.asgi import application


def _ws_path(slug: str, token: str | None = None) -> str:
    if token:
        return f"/ws/c/{slug}/chat?token={token}"
    return f"/ws/c/{slug}/chat"


@database_sync_to_async
def _make_streamer(slug: str = "streamer4"):
    user = UserFactory(username=slug)
    channel = Channel.objects.get(user=user)
    Channel.objects.filter(pk=channel.pk).update(is_live=True)
    channel.refresh_from_db()
    return user, channel


@database_sync_to_async
def _make_user():
    return UserFactory()


def _access_for(user) -> str:
    return str(RefreshToken.for_user(user).access_token)


@pytest.mark.django_db(transaction=True)
async def test_connect_anonymous_when_live_ok():
    _, channel = await _make_streamer("anonok")
    comm = WebsocketCommunicator(application, _ws_path(channel.slug))
    connected, _code = await comm.connect()
    assert connected
    await comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_connect_rejected_when_offline_and_not_streamer():
    user = await _make_user()
    channel = await database_sync_to_async(Channel.objects.get)(user=user)
    # is_live=False par défaut.
    comm = WebsocketCommunicator(application, _ws_path(channel.slug))
    connected, code = await comm.connect()
    assert not connected
    assert code == 4403


@pytest.mark.django_db(transaction=True)
async def test_streamer_can_connect_even_offline():
    user, channel = await _make_streamer("offlinestream")
    # On force offline pour le test.
    await database_sync_to_async(Channel.objects.filter(pk=channel.pk).update)(is_live=False)
    token = _access_for(user)
    comm = WebsocketCommunicator(application, _ws_path(channel.slug, token=token))
    connected, _ = await comm.connect()
    assert connected
    await comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_anonymous_cannot_send():
    _, channel = await _make_streamer("anonomute")
    comm = WebsocketCommunicator(application, _ws_path(channel.slug))
    connected, _ = await comm.connect()
    assert connected
    await comm.send_to(text_data=json.dumps({"content": "hello"}))
    response = await comm.receive_json_from()
    assert response["type"] == "error"
    await comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_authenticated_user_can_send_and_receive():
    _, channel = await _make_streamer("speakok")
    sender = await _make_user()
    token = _access_for(sender)
    comm = WebsocketCommunicator(application, _ws_path(channel.slug, token=token))
    connected, _ = await comm.connect()
    assert connected
    await comm.send_to(text_data=json.dumps({"content": "salut !"}))
    response = await comm.receive_json_from()
    assert response["type"] == "message"
    assert response["msg"]["content"] == "salut !"
    assert response["msg"]["user"]["username"] == sender.username
    await comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_banned_user_cannot_connect():
    _, channel = await _make_streamer("banowner")
    banned = await _make_user()
    await database_sync_to_async(ChatBan.objects.create)(channel=channel, user=banned, until=None)
    token = _access_for(banned)
    comm = WebsocketCommunicator(application, _ws_path(channel.slug, token=token))
    connected, code = await comm.connect()
    assert not connected
    assert code == 4403


@pytest.mark.django_db(transaction=True)
async def test_unknown_channel_returns_4404():
    comm = WebsocketCommunicator(application, _ws_path("ghost"))
    connected, code = await comm.connect()
    assert not connected
    assert code == 4404


@pytest.mark.django_db(transaction=True)
async def test_shadow_banned_user_can_connect():
    _, channel = await _make_streamer("shadowown")
    shadowed = await _make_user()
    await database_sync_to_async(ChatBan.objects.create)(
        channel=channel, user=shadowed, until=None, shadow=True
    )
    token = _access_for(shadowed)
    comm = WebsocketCommunicator(application, _ws_path(channel.slug, token=token))
    connected, _ = await comm.connect()
    assert connected  # shadow ban ne ferme pas la connexion
    await comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_shadow_message_echoed_to_self_only():
    streamer, channel = await _make_streamer("shadowsee")
    shadowed = await _make_user()
    await database_sync_to_async(ChatBan.objects.create)(
        channel=channel, user=shadowed, until=None, shadow=True
    )

    obs = WebsocketCommunicator(application, _ws_path(channel.slug, token=_access_for(streamer)))
    assert (await obs.connect())[0]
    shadow_comm = WebsocketCommunicator(
        application, _ws_path(channel.slug, token=_access_for(shadowed))
    )
    assert (await shadow_comm.connect())[0]

    await shadow_comm.send_to(text_data=json.dumps({"content": "invisible"}))
    own = await shadow_comm.receive_json_from()
    assert own["type"] == "message"
    assert own["msg"]["content"] == "invisible"

    # L'observateur (streamer) ne reçoit jamais le message shadow-banni.
    assert await obs.receive_nothing(timeout=0.3)

    await shadow_comm.disconnect()
    await obs.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_ip_banned_connection_rejected():
    from chat.models import ChatIpBan

    _, channel = await _make_streamer("ipbanown")
    await database_sync_to_async(ChatIpBan.objects.create)(
        channel=channel, ip="9.9.9.9", until=None
    )
    comm = WebsocketCommunicator(
        application, _ws_path(channel.slug), headers=[(b"x-forwarded-for", b"9.9.9.9")]
    )
    connected, code = await comm.connect()
    assert not connected
    assert code == 4403


@pytest.mark.django_db(transaction=True)
async def test_connect_records_user_ip():
    from chat.models import ChatUserIp

    _, channel = await _make_streamer("iptrack")
    fan = await _make_user()
    comm = WebsocketCommunicator(
        application,
        _ws_path(channel.slug, token=_access_for(fan)),
        headers=[(b"x-forwarded-for", b"5.5.5.5")],
    )
    assert (await comm.connect())[0]
    await comm.disconnect()
    ip = await database_sync_to_async(
        lambda: ChatUserIp.objects.get(channel=channel, user=fan).ip
    )()
    assert ip == "5.5.5.5"


@pytest.mark.django_db(transaction=True)
async def test_ipban_command_bans_user_ip():
    from chat.models import ChatIpBan

    streamer, channel = await _make_streamer("ipcmd")
    fan = await _make_user()

    fan_comm = WebsocketCommunicator(
        application,
        _ws_path(channel.slug, token=_access_for(fan)),
        headers=[(b"x-forwarded-for", b"5.5.5.5")],
    )
    assert (await fan_comm.connect())[0]

    streamer_comm = WebsocketCommunicator(
        application, _ws_path(channel.slug, token=_access_for(streamer))
    )
    assert (await streamer_comm.connect())[0]

    await streamer_comm.send_to(text_data=json.dumps({"content": f"/ipban {fan.username}"}))
    # Le streamer reçoit la confirmation système.
    sys_msg = await streamer_comm.receive_json_from(timeout=1)
    assert sys_msg["type"] == "system"

    banned = await database_sync_to_async(
        lambda: ChatIpBan.objects.filter(channel=channel, ip="5.5.5.5").exists()
    )()
    assert banned

    await fan_comm.disconnect()
    await streamer_comm.disconnect()

    # Nouvelle connexion depuis l'IP bannie → refusée.
    again = WebsocketCommunicator(
        application, _ws_path(channel.slug), headers=[(b"x-forwarded-for", b"5.5.5.5")]
    )
    connected, code = await again.connect()
    assert not connected
    assert code == 4403
