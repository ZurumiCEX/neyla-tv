"""Upload d'images vers Cloudflare R2 (S3-compatible).

Mode FAKE automatique si R2 non configuré : renvoie une URL `fake.local` sans
appel réseau (dev/tests/local) — même approche que le client Cloudflare Stream.
Formats acceptés : PNG, JPEG, WebP. Taille max : 5 Mo.
"""

from __future__ import annotations

import logging
import secrets

from django.conf import settings

logger = logging.getLogger(__name__)

ALLOWED = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
MAX_BYTES = 5 * 1024 * 1024


class UploadError(Exception):
    """Format/typologie/taille invalide."""


def upload_image(file, folder: str) -> str:
    ext = ALLOWED.get(getattr(file, "content_type", ""))
    if ext is None:
        raise UploadError("Format non supporté (png, jpeg, webp).")
    if getattr(file, "size", 0) > MAX_BYTES:
        raise UploadError("Image trop lourde (max 5 Mo).")
    key = f"{folder}/{secrets.token_hex(16)}.{ext}"
    content_type = file.content_type
    return _put(key, file, content_type)


def _r2_configured() -> bool:
    return bool(
        getattr(settings, "CLOUDFLARE_R2_BUCKET", "")
        and getattr(settings, "CLOUDFLARE_R2_ACCESS_KEY", "")
    )


def _put(key: str, file, content_type: str) -> str:
    if not _r2_configured():
        logger.info("uploads:fake:put key=%s", key)
        base = getattr(settings, "CLOUDFLARE_R2_PUBLIC_BASE_URL", "") or "https://fake.local"
        return f"{base}/{key}"
    import boto3

    client = boto3.client(
        "s3",
        endpoint_url=settings.CLOUDFLARE_R2_ENDPOINT,
        aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY,
        aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_KEY,
        region_name="auto",
    )
    client.put_object(
        Bucket=settings.CLOUDFLARE_R2_BUCKET,
        Key=key,
        Body=file.read(),
        ContentType=content_type,
    )
    return f"{settings.CLOUDFLARE_R2_PUBLIC_BASE_URL}/{key}"
