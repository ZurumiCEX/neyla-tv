"""Client Bunny Stream (live + VOD) avec un mode FAKE pour dev/tests hors-ligne.

Bunny Stream est l'unique fournisseur vidéo de la plateforme :
- **Live** : un live stream par chaîne (ingest RTMP, lecture HLS).
- **VOD** : vidéos courtes (« Instant » / Shorts), upload direct navigateur
  via TUS signé.

Le mode FAKE est activé automatiquement si `BUNNY_STREAM_API_KEY` est vide.
Il ne fait aucun appel réseau et renvoie un flux HLS public de test pour que le
lecteur fonctionne en démo.

Le schéma de réponse de l'API live Bunny étant peu documenté, l'analyse est
défensive (plusieurs noms de clés essayés). `manage.py verify_bunny_stream`
affiche la réponse brute pour ajuster facilement si besoin.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import time
from dataclasses import dataclass, field

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BUNNY_API_BASE = "https://video.bunnycdn.com"
BUNNY_TUS_ENDPOINT = "https://video.bunnycdn.com/tusupload"
BUNNY_REQUEST_TIMEOUT = 10.0
# Ingest RTMP par défaut (surchargé par la réponse API ou BUNNY_STREAM_RTMP_URL).
DEFAULT_RTMP_URL = "rtmp://live.bunnycdn.com/live"
# Flux HLS public utilisé en mode FAKE pour que le lecteur joue réellement.
FAKE_HLS_URL = (
    "https://devstreaming-cdn.apple.com/videos/streaming/examples/"
    "bipbop_16x9/bipbop_16x9_variant.m3u8"
)


@dataclass(frozen=True)
class LiveStream:
    stream_id: str
    ingest_url: str
    stream_key: str
    playback_url: str
    raw: dict = field(default_factory=dict, compare=False, repr=False)


@dataclass(frozen=True)
class LiveStatus:
    is_live: bool
    raw: dict = field(default_factory=dict, compare=False, repr=False)


@dataclass(frozen=True)
class VideoUpload:
    """Paramètres d'upload TUS direct (navigateur → Bunny)."""

    video_id: str
    library_id: str
    endpoint: str
    expires: int
    signature: str


class BunnyStreamError(Exception):
    """Erreur côté API Bunny Stream."""


def _first(data: dict, *keys: str, default=""):
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return default


def cdn_hostname() -> str:
    return (getattr(settings, "BUNNY_STREAM_CDN_HOSTNAME", "") or "").strip().rstrip("/")


def video_playback_url(video_id: str) -> str:
    host = cdn_hostname()
    return f"https://{host}/{video_id}/playlist.m3u8" if host else ""


def video_thumbnail_url(video_id: str) -> str:
    host = cdn_hostname()
    return f"https://{host}/{video_id}/thumbnail.jpg" if host else ""


def tus_signature(library_id: str, api_key: str, expires: int, video_id: str) -> str:
    """Signature TUS Bunny : sha256(library_id + api_key + expiration + video_id)."""
    raw = f"{library_id}{api_key}{expires}{video_id}".encode()
    return hashlib.sha256(raw).hexdigest()


class BunnyStreamClient:
    """Interface commune FAKE / HTTP."""

    is_fake = False

    # --- Live ---
    def create_live_stream(self, label: str) -> LiveStream:
        raise NotImplementedError

    def delete_live_stream(self, stream_id: str) -> None:
        raise NotImplementedError

    def get_live_status(self, stream_id: str) -> LiveStatus:
        raise NotImplementedError

    # --- VOD ---
    def create_video(self, title: str) -> str:
        raise NotImplementedError

    def delete_video(self, video_id: str) -> None:
        raise NotImplementedError

    def upload_params(self, video_id: str, ttl_seconds: int = 3600) -> VideoUpload:
        raise NotImplementedError


class FakeBunnyStreamClient(BunnyStreamClient):
    """Aucun appel réseau. Utilisé en dev local, CI et démo."""

    is_fake = True

    def create_live_stream(self, label: str) -> LiveStream:
        stream_id = f"fake-{secrets.token_hex(8)}"
        key = f"fake-key-{secrets.token_hex(16)}"
        logger.info("bunny:fake:create_live_stream label=%s id=%s", label, stream_id)
        return LiveStream(
            stream_id=stream_id,
            ingest_url="rtmp://fake.local/live",
            stream_key=key,
            playback_url=FAKE_HLS_URL,
        )

    def delete_live_stream(self, stream_id: str) -> None:
        logger.info("bunny:fake:delete_live_stream id=%s", stream_id)

    def get_live_status(self, stream_id: str) -> LiveStatus:  # noqa: ARG002
        # En FAKE, on ne sait pas : l'état reste piloté par la bascule manuelle.
        return LiveStatus(is_live=False, raw={"fake": True})

    def create_video(self, title: str) -> str:
        video_id = f"fake-video-{secrets.token_hex(8)}"
        logger.info("bunny:fake:create_video title=%s id=%s", title, video_id)
        return video_id

    def delete_video(self, video_id: str) -> None:
        logger.info("bunny:fake:delete_video id=%s", video_id)

    def upload_params(self, video_id: str, ttl_seconds: int = 3600) -> VideoUpload:
        expires = int(time.time()) + ttl_seconds
        return VideoUpload(
            video_id=video_id,
            library_id="fake-library",
            endpoint="",
            expires=expires,
            signature="fake-signature",
        )


class HttpBunnyStreamClient(BunnyStreamClient):
    def __init__(self, library_id: str, api_key: str) -> None:
        if not library_id or not api_key:
            raise BunnyStreamError("Configuration Bunny Stream manquante.")
        self._library_id = str(library_id)
        self._api_key = api_key
        self._session = requests.Session()
        self._session.headers.update({"AccessKey": api_key, "Accept": "application/json"})

    def _url(self, *parts: str) -> str:
        joined = "/".join(p.strip("/") for p in parts)
        return f"{BUNNY_API_BASE}/library/{self._library_id}/{joined}"

    def _request(self, method: str, url: str, **kwargs) -> dict:
        try:
            resp = self._session.request(method, url, timeout=BUNNY_REQUEST_TIMEOUT, **kwargs)
        except requests.RequestException as exc:
            raise BunnyStreamError(str(exc)) from exc
        if method == "DELETE" and resp.status_code == 404:
            return {}  # déjà supprimé : idempotent.
        if resp.status_code >= 400:
            raise BunnyStreamError(f"{method} {url} → {resp.status_code}: {resp.text[:300]}")
        if not resp.content:
            return {}
        try:
            payload = resp.json()
        except ValueError:
            return {}
        return payload if isinstance(payload, dict) else {"data": payload}

    # --- Live ---
    def create_live_stream(self, label: str) -> LiveStream:
        data = self._request("POST", self._url("live"), json={"name": label})
        stream_id = str(_first(data, "id", "guid", "streamId", "liveStreamId"))
        if not stream_id:
            raise BunnyStreamError(f"Réponse Bunny incomplète (id manquant) : {data}")
        override_rtmp = getattr(settings, "BUNNY_STREAM_RTMP_URL", "") or ""
        ingest = override_rtmp or _first(
            data, "rtmpUrl", "ingestUrl", "rtmpIngestUrl", "serverUrl", default=DEFAULT_RTMP_URL
        )
        key = str(_first(data, "streamKey", "rtmpKey", "key"))
        playback = _first(data, "playbackUrl", "hlsUrl", "hlsPlaybackUrl") or (
            video_playback_url(stream_id)
        )
        return LiveStream(
            stream_id=stream_id,
            ingest_url=str(ingest),
            stream_key=key,
            playback_url=str(playback),
            raw=data,
        )

    def delete_live_stream(self, stream_id: str) -> None:
        self._request("DELETE", self._url("live", stream_id))

    def get_live_status(self, stream_id: str) -> LiveStatus:
        data = self._request("GET", self._url("live", stream_id))
        flag = _first(data, "isLive", "live", "isOnline", "online", default=None)
        if isinstance(flag, bool):
            return LiveStatus(is_live=flag, raw=data)
        status = str(_first(data, "status", "state", default="")).lower()
        return LiveStatus(
            is_live=status in {"live", "online", "streaming", "started", "active", "connected"},
            raw=data,
        )

    # --- VOD ---
    def create_video(self, title: str) -> str:
        data = self._request("POST", self._url("videos"), json={"title": title[:200]})
        video_id = str(_first(data, "guid", "id"))
        if not video_id:
            raise BunnyStreamError(f"Réponse Bunny incomplète (guid manquant) : {data}")
        return video_id

    def delete_video(self, video_id: str) -> None:
        self._request("DELETE", self._url("videos", video_id))

    def upload_params(self, video_id: str, ttl_seconds: int = 3600) -> VideoUpload:
        expires = int(time.time()) + ttl_seconds
        return VideoUpload(
            video_id=video_id,
            library_id=self._library_id,
            endpoint=BUNNY_TUS_ENDPOINT,
            expires=expires,
            signature=tus_signature(self._library_id, self._api_key, expires, video_id),
        )


def get_client() -> BunnyStreamClient:
    """Retourne le client réel ou FAKE selon la présence de la clé API."""
    api_key = getattr(settings, "BUNNY_STREAM_API_KEY", "") or ""
    if not api_key:
        return FakeBunnyStreamClient()
    return HttpBunnyStreamClient(
        library_id=getattr(settings, "BUNNY_STREAM_LIBRARY_ID", ""),
        api_key=api_key,
    )
