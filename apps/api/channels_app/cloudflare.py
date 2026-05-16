"""Client Cloudflare Stream avec un mode FAKE pour dev/tests hors-ligne.

Le mode FAKE est activé automatiquement si `CLOUDFLARE_API_TOKEN` est vide.
Il génère des URLs `rtmps://fake.local/...` et `https://fake.local/...m3u8`
pour pouvoir développer toute la stack sans dépendre du réseau Cloudflare.
"""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

CF_API_BASE = "https://api.cloudflare.com/client/v4"
CF_REQUEST_TIMEOUT = 10.0


@dataclass(frozen=True)
class LiveInput:
    uid: str
    rtmps_url: str
    rtmps_key: str
    hls_playback_url: str


class CloudflareStreamError(Exception):
    """Erreur côté API Cloudflare Stream."""


class CloudflareStreamClient:
    """Interface commune entre FAKE et HTTP."""

    def create_live_input(self, label: str) -> LiveInput:
        raise NotImplementedError

    def delete_live_input(self, uid: str) -> None:
        raise NotImplementedError


class FakeCloudflareStreamClient(CloudflareStreamClient):
    """Pas d'appel réseau. Utile pour dev local et CI."""

    def create_live_input(self, label: str) -> LiveInput:
        uid = f"fake-{secrets.token_hex(8)}"
        key = f"fake-key-{secrets.token_hex(16)}"
        logger.info("cloudflare:fake:create_live_input label=%s uid=%s", label, uid)
        return LiveInput(
            uid=uid,
            rtmps_url="rtmps://fake.local/live",
            rtmps_key=key,
            hls_playback_url=f"https://fake.local/{uid}/manifest.m3u8",
        )

    def delete_live_input(self, uid: str) -> None:
        logger.info("cloudflare:fake:delete_live_input uid=%s", uid)


class HttpCloudflareStreamClient(CloudflareStreamClient):
    def __init__(self, account_id: str, api_token: str) -> None:
        if not account_id or not api_token:
            raise CloudflareStreamError("Configuration Cloudflare manquante.")
        self._account_id = account_id
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Bearer {api_token}"

    def _url(self, *parts: str) -> str:
        joined = "/".join(parts)
        return f"{CF_API_BASE}/accounts/{self._account_id}/stream/{joined}"

    def create_live_input(self, label: str) -> LiveInput:
        try:
            resp = self._session.post(
                self._url("live_inputs"),
                json={"meta": {"name": label}, "recording": {"mode": "off"}},
                timeout=CF_REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise CloudflareStreamError(str(exc)) from exc
        data = resp.json().get("result") or {}
        try:
            return LiveInput(
                uid=data["uid"],
                rtmps_url=data["rtmps"]["url"],
                rtmps_key=data["rtmps"]["streamKey"],
                hls_playback_url=data["playback"]["hls"],
            )
        except KeyError as exc:
            raise CloudflareStreamError(f"Réponse Cloudflare incomplète : {exc}") from exc

    def delete_live_input(self, uid: str) -> None:
        try:
            resp = self._session.delete(
                self._url("live_inputs", uid),
                timeout=CF_REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise CloudflareStreamError(str(exc)) from exc
        # 404 = déjà supprimé : on accepte, c'est idempotent.
        if resp.status_code not in (200, 204, 404):
            raise CloudflareStreamError(f"DELETE live_input {uid} → {resp.status_code}")


def get_client() -> CloudflareStreamClient:
    """Retourne le client réel ou FAKE selon la présence du token."""
    if not settings.CLOUDFLARE_API_TOKEN:
        return FakeCloudflareStreamClient()
    return HttpCloudflareStreamClient(
        account_id=settings.CLOUDFLARE_ACCOUNT_ID,
        api_token=settings.CLOUDFLARE_API_TOKEN,
    )
