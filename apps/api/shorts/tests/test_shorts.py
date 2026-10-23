"""Tests « Instant » : upload (FAKE), webhook Bunny, fil tendance, vues, likes."""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from accounts.factories import UserFactory
from channels_app.testing import provisioned_channel
from shorts import services
from shorts.models import Short

pytestmark = pytest.mark.django_db


def _ready_short(channel, title="clip", views=0, likes=0, hours_ago=1):
    return Short.objects.create(
        channel=channel,
        title=title,
        video_guid=f"g-{title}",
        status=Short.Status.READY,
        playback_url="https://cdn.example/x/playlist.m3u8",
        view_count=views,
        like_count=likes,
        published_at=timezone.now() - timezone.timedelta(hours=hours_ago),
    )


def test_only_approved_streamers_can_upload():
    with pytest.raises(services.ShortError):
        services.create_upload(UserFactory(), "Mon clip")


def test_fake_upload_publishes_immediately():
    user = UserFactory()
    provisioned_channel(user)
    short, upload = services.create_upload(user, "Mon premier Instant")
    assert upload == {"mode": "fake"}
    short.refresh_from_db()
    assert short.status == Short.Status.READY
    assert short.playback_url


def test_pending_uploads_capped():
    user = UserFactory()
    channel = provisioned_channel(user)
    for i in range(services.MAX_PENDING_UPLOADS):
        Short.objects.create(channel=channel, title=f"t{i}", video_guid=f"p{i}")
    with pytest.raises(services.ShortError):
        services.create_upload(user, "Encore un")


def _sign(body: bytes) -> dict:
    sig = hmac.new(settings.BUNNY_STREAM_WEBHOOK_KEY.encode(), body, hashlib.sha256).hexdigest()
    return {"HTTP_X_BUNNYSTREAM_SIGNATURE": sig}


def test_bunny_webhook_marks_short_ready_then_failed(client, settings):
    settings.BUNNY_STREAM_CDN_HOSTNAME = "vz-demo.b-cdn.net"
    channel = provisioned_channel(UserFactory())
    short = Short.objects.create(
        channel=channel, title="encodage", video_guid="vid-1", status=Short.Status.PROCESSING
    )
    body = json.dumps({"VideoLibraryId": 1, "VideoGuid": "vid-1", "Status": 3}).encode()
    resp = client.post(
        reverse("bunny-stream-webhook"), data=body, content_type="application/json", **_sign(body)
    )
    assert resp.status_code == 200
    short.refresh_from_db()
    assert short.status == Short.Status.READY
    assert short.playback_url == "https://vz-demo.b-cdn.net/vid-1/playlist.m3u8"
    assert short.thumbnail_url.endswith("/vid-1/thumbnail.jpg")

    other = Short.objects.create(channel=channel, title="ko", video_guid="vid-2")
    body = json.dumps({"VideoGuid": "vid-2", "Status": 5}).encode()
    client.post(
        reverse("bunny-stream-webhook"), data=body, content_type="application/json", **_sign(body)
    )
    other.refresh_from_db()
    assert other.status == Short.Status.FAILED


def test_trending_ranks_by_popularity_and_freshness(api_client):
    a = provisioned_channel(UserFactory())
    b = provisioned_channel(UserFactory())
    old_hit = _ready_short(a, "vieux", views=500, hours_ago=24 * 30)
    fresh_hit = _ready_short(b, "frais", views=200, likes=20, hours_ago=2)
    quiet = _ready_short(b, "calme", views=1, hours_ago=3)
    Short.objects.create(channel=a, title="encodage", video_guid="busy")  # pas prête
    hidden = _ready_short(a, "masque", views=10_000)
    hidden.is_published = False
    hidden.save()

    data = api_client.get(reverse("shorts-trending")).json()["results"]
    ids = [s["id"] for s in data]
    assert ids[0] == fresh_hit.id
    assert set(ids) == {fresh_hit.id, quiet.id, old_hit.id}
    assert data[0]["channel"]["slug"] == b.slug


def test_view_counted_once_per_viewer(api_client):
    short = _ready_short(provisioned_channel(UserFactory()))
    url = reverse("shorts-view", kwargs={"pk": short.pk})
    first = api_client.post(url).json()["counted"]
    api_client.post(url)
    short.refresh_from_db()
    assert first is True
    assert short.view_count == 1


def test_like_and_unlike(auth_client_factory):
    short = _ready_short(provisioned_channel(UserFactory()))
    client = auth_client_factory(UserFactory())
    url = reverse("shorts-like", kwargs={"pk": short.pk})
    assert client.post(url).json()["like_count"] == 1
    assert client.post(url).json()["like_count"] == 1  # idempotent
    detail = client.get(reverse("shorts-detail", kwargs={"pk": short.pk})).json()
    assert detail["liked"] is True
    assert client.delete(url).json()["like_count"] == 0


def test_like_requires_auth(api_client):
    short = _ready_short(provisioned_channel(UserFactory()))
    assert api_client.post(reverse("shorts-like", kwargs={"pk": short.pk})).status_code == 401


def test_owner_can_list_and_delete(auth_client_factory):
    user = UserFactory()
    provisioned_channel(user)
    client = auth_client_factory(user)
    created = client.post(reverse("shorts-mine"), {"title": "Highlight"}, format="json")
    assert created.status_code == 201
    sid = created.json()["short"]["id"]
    assert [s["id"] for s in client.get(reverse("shorts-mine")).json()["results"]] == [sid]
    other = auth_client_factory(UserFactory())
    assert other.delete(reverse("shorts-mine-delete", kwargs={"pk": sid})).status_code == 404
    assert client.delete(reverse("shorts-mine-delete", kwargs={"pk": sid})).status_code == 204
    assert not Short.objects.filter(pk=sid).exists()
