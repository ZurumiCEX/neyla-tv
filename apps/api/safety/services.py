"""Orchestration anti-violation : scanne un contenu, crée un ContentFlag et
déclenche les actions automatiques (file de modération + audit).
"""

from __future__ import annotations

import contextlib
import logging

from django.utils import timezone

from . import scanner
from .models import ContentFlag

logger = logging.getLogger(__name__)


def scan_text(text: str, source: str, *, user=None, channel=None) -> ContentFlag | None:
    """Scanne un texte ; crée un flag si non-sain. Best-effort."""
    result = scanner.classify_text(text)
    if result.category in ("safe", "unknown"):
        return None
    return _create_flag(
        source=source,
        category=result.category,
        confidence=result.confidence,
        scores=result.scores,
        text=text[:500],
        user=user,
        channel=channel,
    )


def scan_image(url: str, source: str, *, user=None, channel=None) -> ContentFlag | None:
    """Scanne une image. Sans fournisseur de vision → file d'examen si activé."""
    if not url:
        return None
    result = scanner.classify_image(url)
    if result.category == "unknown":
        from django.conf import settings

        if not getattr(settings, "SAFETY_REVIEW_UPLOADS", False):
            return None
        return _create_flag(
            source=source,
            category=ContentFlag.Category.OTHER,
            confidence=0.0,
            scores={"reason": "manual_review"},
            url=url,
            user=user,
            channel=channel,
            status=ContentFlag.Status.PENDING,
        )
    if result.category == "safe":
        return None
    return _create_flag(
        source=source,
        category=result.category,
        confidence=result.confidence,
        scores=result.scores,
        url=url,
        user=user,
        channel=channel,
    )


def _create_flag(
    *,
    source: str,
    category: str,
    confidence: float,
    scores: dict,
    text: str = "",
    url: str = "",
    user=None,
    channel=None,
    status: str | None = None,
) -> ContentFlag:
    violation = category in (ContentFlag.Category.SEXUAL, ContentFlag.Category.GORE)
    if status is None:
        status = ContentFlag.Status.AUTO_BLOCKED if violation else ContentFlag.Status.PENDING
    if user is None and channel is not None:
        user = channel.user
    flag = ContentFlag.objects.create(
        user=user,
        channel=channel,
        source=source,
        category=category,
        confidence=confidence,
        scores=scores,
        text=text,
        url=url,
        status=status,
    )
    if violation:
        _auto_action(flag)
    return flag


def _auto_action(flag: ContentFlag) -> None:
    """Crée un signalement de modération + trace d'audit pour une violation."""
    with contextlib.suppress(Exception):
        from moderation.models import Report

        Report.objects.create(
            reporter=flag.user or flag.channel.user,
            target_user=flag.user,
            channel=flag.channel,
            reason=Report.Reason.OTHER,
            details=f"[auto-safety] {flag.get_category_display()} sur {flag.get_source_display()}"
            + (f" : {flag.text}" if flag.text else ""),
        )
    with contextlib.suppress(Exception):
        from audit.services import record

        record(
            flag.user,
            "safety.content_blocked",
            target=flag,
            meta={"source": flag.source, "category": flag.category},
        )


def resolve_flag(flag: ContentFlag, reviewer, approve: bool) -> ContentFlag:
    flag.status = ContentFlag.Status.APPROVED if approve else ContentFlag.Status.REJECTED
    flag.reviewed_by = reviewer
    flag.resolved_at = timezone.now()
    flag.save(update_fields=["status", "reviewed_by", "resolved_at"])
    return flag
