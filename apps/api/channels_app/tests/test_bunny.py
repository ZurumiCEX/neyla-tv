"""Tests du client Bunny Stream (FAKE + HTTP mocké via responses)."""

from __future__ import annotations

import pytest
import responses
from django.test import override_settings

from channels_app.bunny import (
    FAKE_HLS_URL,
    BunnyStreamError,
    FakeBunnyStreamClient,
    HttpBunnyStreamClient,
    get_client,
    tus_signature,
)

LIVE_URL = "https://video.bunnycdn.com/library/42/live"


def test_fake_client_returns_consistent_urls():
    client = FakeBunnyStreamClient()
    a = client.create_live_stream("ch1")
    b = client.create_live_stream("ch2")
    assert a.stream_id != b.stream_id
    assert a.ingest_url == "rtmp://fake.local/live"
    assert a.stream_key.startswith("fake-key-")
    assert a.playback_url == FAKE_HLS_URL


@override_settings(BUNNY_STREAM_API_KEY="", BUNNY_STREAM_LIBRARY_ID="")
def test_get_client_returns_fake_when_no_key():
    assert isinstance(get_client(), FakeBunnyStreamClient)


@override_settings(BUNNY_STREAM_API_KEY="key", BUNNY_STREAM_LIBRARY_ID="42")
def test_get_client_returns_http_when_key_present():
    assert isinstance(get_client(), HttpBunnyStreamClient)


@responses.activate
@override_settings(BUNNY_STREAM_CDN_HOSTNAME="vz-test.b-cdn.net", BUNNY_STREAM_RTMP_URL="")
def test_http_client_create_parses_payload_and_sends_access_key():
    responses.add(
        responses.POST,
        LIVE_URL,
        json={"id": "live-1", "streamKey": "sk_xyz", "rtmpUrl": "rtmp://ingest.b-cdn.net/live"},
        status=200,
    )
    live = HttpBunnyStreamClient(library_id="42", api_key="key").create_live_stream("ch")
    assert responses.calls[0].request.headers["AccessKey"] == "key"
    assert live.stream_id == "live-1"
    assert live.stream_key == "sk_xyz"
    assert live.ingest_url == "rtmp://ingest.b-cdn.net/live"
    # Pas d'URL de lecture dans la réponse → repli sur le CDN de la bibliothèque.
    assert live.playback_url == "https://vz-test.b-cdn.net/live-1/playlist.m3u8"


@responses.activate
def test_http_client_create_raises_on_error():
    responses.add(responses.POST, LIVE_URL, json={"Message": "boom"}, status=500)
    with pytest.raises(BunnyStreamError):
        HttpBunnyStreamClient(library_id="42", api_key="key").create_live_stream("ch")


@responses.activate
def test_http_client_create_raises_when_id_missing():
    responses.add(responses.POST, LIVE_URL, json={"streamKey": "x"}, status=200)
    with pytest.raises(BunnyStreamError):
        HttpBunnyStreamClient(library_id="42", api_key="key").create_live_stream("ch")


@responses.activate
def test_http_client_delete_is_idempotent_on_404():
    responses.add(responses.DELETE, f"{LIVE_URL}/gone", status=404)
    HttpBunnyStreamClient(library_id="42", api_key="key").delete_live_stream("gone")


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"isLive": True}, True),
        ({"isLive": False}, False),
        ({"status": "Live"}, True),
        ({"status": "offline"}, False),
        ({}, False),
    ],
)
@responses.activate
def test_http_client_live_status_parsing(payload, expected):
    responses.add(responses.GET, f"{LIVE_URL}/s1", json=payload, status=200)
    status = HttpBunnyStreamClient(library_id="42", api_key="key").get_live_status("s1")
    assert status.is_live is expected


def test_tus_signature_matches_bunny_formula():
    import hashlib

    expected = hashlib.sha256(b"42key1700000000vid").hexdigest()
    assert tus_signature("42", "key", 1700000000, "vid") == expected
