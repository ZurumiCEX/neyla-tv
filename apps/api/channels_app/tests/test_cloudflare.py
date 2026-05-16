"""Tests du client Cloudflare (FAKE + HTTP mocké via responses)."""

from __future__ import annotations

import pytest
import responses
from django.test import override_settings

from channels_app.cloudflare import (
    CloudflareStreamError,
    FakeCloudflareStreamClient,
    HttpCloudflareStreamClient,
    get_client,
)


def test_fake_client_returns_consistent_urls():
    client = FakeCloudflareStreamClient()
    a = client.create_live_input("ch1")
    b = client.create_live_input("ch2")
    assert a.uid != b.uid
    assert a.rtmps_url == "rtmps://fake.local/live"
    assert a.hls_playback_url.endswith("manifest.m3u8")


@override_settings(CLOUDFLARE_API_TOKEN="", CLOUDFLARE_ACCOUNT_ID="")
def test_get_client_returns_fake_when_no_token():
    assert isinstance(get_client(), FakeCloudflareStreamClient)


@override_settings(CLOUDFLARE_API_TOKEN="tok", CLOUDFLARE_ACCOUNT_ID="acct")
def test_get_client_returns_http_when_token_present():
    assert isinstance(get_client(), HttpCloudflareStreamClient)


@responses.activate
def test_http_client_create_parses_payload():
    responses.add(
        responses.POST,
        "https://api.cloudflare.com/client/v4/accounts/acct/stream/live_inputs",
        json={
            "result": {
                "uid": "abc123",
                "rtmps": {"url": "rtmps://live.cloudflare.com/live/", "streamKey": "sk_xyz"},
                "playback": {"hls": "https://cf.tv/abc123/manifest.m3u8"},
            }
        },
        status=200,
    )
    client = HttpCloudflareStreamClient(account_id="acct", api_token="tok")
    live = client.create_live_input("ch")
    assert live.uid == "abc123"
    assert live.rtmps_key == "sk_xyz"
    assert live.hls_playback_url.endswith("manifest.m3u8")


@responses.activate
def test_http_client_create_raises_on_error():
    responses.add(
        responses.POST,
        "https://api.cloudflare.com/client/v4/accounts/acct/stream/live_inputs",
        json={"errors": [{"message": "boom"}]},
        status=500,
    )
    client = HttpCloudflareStreamClient(account_id="acct", api_token="tok")
    with pytest.raises(CloudflareStreamError):
        client.create_live_input("ch")


@responses.activate
def test_http_client_delete_is_idempotent_on_404():
    responses.add(
        responses.DELETE,
        "https://api.cloudflare.com/client/v4/accounts/acct/stream/live_inputs/gone",
        status=404,
    )
    client = HttpCloudflareStreamClient(account_id="acct", api_token="tok")
    client.delete_live_input("gone")
