"""Dashboard streamer : réglages du chat appliqués en direct, journal, déban, activité."""

from __future__ import annotations

import json

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.factories import UserFactory
from channels_app.models import Channel
from channels_app.testing import provisioned_channel
from chat.models import ChannelBannedWord, ChatBan, ModAction, UnbanRequest
from config.asgi import application
from payments import services as pay
from safety.automod import check
from subscriptions import services as subs


@database_sync_to_async
def _live_channel(slug: str, **settings):
    user = UserFactory(username=slug)
    Channel.objects.filter(user=user).update(is_live=True, **settings)
    return user, Channel.objects.get(user=user)


@database_sync_to_async
def _token(user) -> str:
    return str(RefreshToken.for_user(user).access_token)


async def _say(channel, user, text: str) -> dict:
    comm = WebsocketCommunicator(
        application, f"/ws/c/{channel.slug}/chat?token={await _token(user)}"
    )
    connected, _ = await comm.connect()
    assert connected
    await comm.send_to(text_data=json.dumps({"content": text}))
    response = await comm.receive_json_from()
    await comm.disconnect()
    return response


@pytest.mark.django_db(transaction=True)
async def test_subscribers_only_blocks_non_subscriber_but_not_streamer():
    owner, channel = await _live_channel("subonly", chat_subscribers_only=True)
    viewer = await database_sync_to_async(UserFactory)()
    blocked = await _say(channel, viewer, "salut")
    assert blocked["type"] == "error"
    assert "abonnés" in blocked["detail"]
    ok = await _say(channel, owner, "bienvenue")
    assert ok["type"] == "message"


@pytest.mark.django_db(transaction=True)
async def test_emotes_only_and_channel_banned_words():
    _, channel = await _live_channel("emotes", chat_emotes_only=True)
    viewer = await database_sync_to_async(UserFactory)()
    assert (await _say(channel, viewer, "texte"))["type"] == "error"
    assert (await _say(channel, viewer, "🔥 🔥"))["type"] == "message"

    _, other = await _live_channel("words")
    await database_sync_to_async(ChannelBannedWord.objects.create)(channel=other, word="arnaque")
    assert (await _say(other, viewer, "c'est une ARNAQUE"))["type"] == "error"


@pytest.mark.django_db(transaction=True)
async def test_automod_blocks_and_logs():
    _, channel = await _live_channel("automod", automod={"bullying": 3, "spam": True})
    viewer = await database_sync_to_async(UserFactory)()
    assert (await _say(channel, viewer, "quel idiot"))["type"] == "error"
    assert (await _say(channel, viewer, "va sur www.promo.com"))["type"] == "error"
    logged = await database_sync_to_async(
        lambda: list(ModAction.objects.filter(channel=channel).values_list("action", flat=True))
    )()
    assert logged == ["automod", "automod"]


@pytest.mark.django_db(transaction=True)
async def test_mod_commands_are_logged():
    owner, channel = await _live_channel("logs")
    target = await database_sync_to_async(UserFactory)(username="troll")
    comm = WebsocketCommunicator(
        application, f"/ws/c/{channel.slug}/chat?token={await _token(owner)}"
    )
    await comm.connect()
    await comm.send_to(text_data=json.dumps({"content": "/timeout troll 5"}))
    await comm.receive_json_from()
    await comm.disconnect()
    action = await database_sync_to_async(ModAction.objects.get)(channel=channel)
    assert action.action == "timeout"
    assert action.duration_s == 300
    assert action.target_user_id == target.id


def test_automod_levels():
    assert check("tu es un idiot", {"bullying": 2}) is None
    assert check("tu es un idiot", {"bullying": 3}) == "bullying"
    assert check("kgvjbwklrgjb", {"gibberish": True}) == "gibberish"
    assert check("GG la team !", dict.fromkeys(("sexual", "hate", "bullying"), 3)) is None


@pytest.mark.django_db
def test_chat_settings_api(auth_client_factory):
    owner = UserFactory()
    client = auth_client_factory(owner)
    data = client.get(reverse("channel-chat-settings")).json()
    assert data["chat_subscribers_only"] is False
    assert data["automod"]["hate"] == 0
    resp = client.patch(
        reverse("channel-chat-settings"),
        {"chat_slow_seconds": 9999, "chat_followers_only": True, "automod": {"hate": 3}},
        format="json",
    ).json()
    assert resp["chat_slow_seconds"] == 600  # borné
    assert resp["chat_followers_only"] is True
    assert resp["automod"]["hate"] == 3
    assert ModAction.objects.filter(action="settings").exists()

    client.post(reverse("channel-banned-words"), {"word": "  Spam  Link "}, format="json")
    words = client.get(reverse("channel-banned-words")).json()["results"]
    assert [w["word"] for w in words] == ["spam link"]


@pytest.mark.django_db
def test_unban_request_flow(auth_client_factory):
    owner = UserFactory()
    channel = Channel.objects.get(user=owner)
    viewer = UserFactory()
    ChatBan.objects.create(channel=channel, user=viewer, until=None)
    vclient = auth_client_factory(viewer)
    url = reverse("chat-unban-request", kwargs={"slug": channel.slug})
    assert vclient.get(url).json() == {"banned": True, "pending": False}
    assert vclient.post(url, {"message": "court"}, format="json").status_code == 400
    assert (
        vclient.post(
            url, {"message": "Désolé, je ne recommencerai plus."}, format="json"
        ).status_code
        == 201
    )
    assert (
        vclient.post(url, {"message": "Encore une demande ici."}, format="json").status_code == 409
    )

    oclient = auth_client_factory(owner)
    pending = oclient.get(reverse("channel-unban-requests")).json()["results"]
    assert len(pending) == 1
    resp = oclient.post(
        reverse("channel-unban-decide", kwargs={"pk": pending[0]["id"]}),
        {"decision": "approve"},
        format="json",
    )
    assert resp.json()["status"] == "approved"
    assert not ChatBan.objects.filter(channel=channel, user=viewer).exists()
    assert UnbanRequest.objects.get().status == "approved"


@pytest.mark.django_db
def test_my_channel_keeps_counters_and_feed_has_gifts(
    auth_client_factory, django_capture_on_commit_callbacks
):
    channel = provisioned_channel(UserFactory())
    subs.set_tier(channel, price_aura=100, perks=[])
    fan, friend = UserFactory(), UserFactory()
    pay.create_purchase(fan, 1_000)
    with django_capture_on_commit_callbacks(execute=True):
        subs.subscribe(fan, channel.slug)
        subs.gift_subscription(fan, channel.slug, friend.username)
    client = auth_client_factory(channel.user)
    patched = client.patch(reverse("channel-me"), {"title": "Nouveau titre"}, format="json").json()
    assert patched["title"] == "Nouveau titre"
    assert patched["active_subs"] == 2
    assert "follower_count" in patched and "viewers" in patched
    feed = client.get(reverse("channel-activity")).json()["results"]
    kinds = [e["type"] for e in feed]
    assert "gift" in kinds and "subscribe" in kinds
    gift = next(e for e in feed if e["type"] == "gift")
    assert gift["target"] == (friend.display_name or friend.username)
    subscribers = client.get(reverse("channel-subscribers")).json()
    assert subscribers["count"] == 2
