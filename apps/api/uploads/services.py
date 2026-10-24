"""Upload d'images vers Cloudflare R2 (S3-compatible).

Sans R2 complet (endpoint, bucket, clés, URL publique), mode LOCAL : le fichier
est réellement écrit dans MEDIA_ROOT et servi par l'API (`/api/media/...`).
Les images s'affichent donc en dev / démo, sans service externe.
Formats acceptés : PNG, JPEG, WebP (signature du fichier vérifiée). Max 5 Mo.
"""

from __future__ import annotations

import logging
import secrets

from django.conf import settings
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)

ALLOWED = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
MAX_BYTES = 5 * 1024 * 1024
MEDIA_PREFIX = "/api/media/"


class UploadError(Exception):
    """Format/typologie/taille invalide."""


def _sniff(head: bytes) -> str | None:
    """Type réel d'après les premiers octets (le content-type client n'est pas fiable)."""
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return None


def upload_image(file, folder: str, request=None, replaces: str = "") -> str:
    """Stocke l'image et renvoie son URL absolue. `replaces` : ancienne URL à supprimer."""
    if getattr(file, "size", 0) > MAX_BYTES:
        raise UploadError("Image trop lourde (max 5 Mo).")
    head = file.read(12)
    file.seek(0)
    content_type = _sniff(head)
    if content_type is None or ALLOWED.get(getattr(file, "content_type", "")) is None:
        raise UploadError("Format non supporté (png, jpeg, webp).")
    key = f"{folder}/{secrets.token_hex(16)}.{ALLOWED[content_type]}"
    url = _put(key, file, content_type, request)
    if replaces:
        delete_image(replaces)
    return url


def r2_configured() -> bool:
    return all(
        getattr(settings, name, "")
        for name in (
            "CLOUDFLARE_R2_ENDPOINT",
            "CLOUDFLARE_R2_BUCKET",
            "CLOUDFLARE_R2_ACCESS_KEY",
            "CLOUDFLARE_R2_SECRET_KEY",
            "CLOUDFLARE_R2_PUBLIC_BASE_URL",
        )
    )


def _client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=settings.CLOUDFLARE_R2_ENDPOINT,
        aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY,
        aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_KEY,
        region_name="auto",
    )


def _put(key: str, file, content_type: str, request=None) -> str:
    if not r2_configured():
        saved = default_storage.save(f"uploads/{key}", file)
        logger.info("uploads:local:put key=%s", saved)
        path = f"{MEDIA_PREFIX}{saved}"
        return request.build_absolute_uri(path) if request is not None else path
    try:
        _client().put_object(
            Bucket=settings.CLOUDFLARE_R2_BUCKET,
            Key=key,
            Body=file.read(),
            ContentType=content_type,
        )
    except Exception as exc:  # noqa: BLE001 - erreur réseau / identifiants R2
        logger.exception("uploads:r2:put_failed key=%s", key)
        raise UploadError("Stockage indisponible, réessaie dans un instant.") from exc
    return f"{settings.CLOUDFLARE_R2_PUBLIC_BASE_URL.rstrip('/')}/{key}"


def delete_image(url: str) -> None:
    """Supprime une image précédemment uploadée (best effort, ignore les URLs externes)."""
    try:
        if MEDIA_PREFIX in url:
            name = url.split(MEDIA_PREFIX, 1)[1]
            if name.startswith("uploads/") and ".." not in name:
                default_storage.delete(name)
            return
        base = getattr(settings, "CLOUDFLARE_R2_PUBLIC_BASE_URL", "").rstrip("/")
        if r2_configured() and base and url.startswith(base + "/"):
            _client().delete_object(Bucket=settings.CLOUDFLARE_R2_BUCKET, Key=url[len(base) + 1 :])
    except Exception:  # noqa: BLE001 - nettoyage best effort
        logger.warning("uploads:delete_failed url=%s", url)
