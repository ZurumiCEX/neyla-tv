"""Services modération : mots interdits + création/traitement de signalements."""

from __future__ import annotations

import re

from django.utils import timezone

from .models import BannedWord, Report

_SPLIT_RE = re.compile(r"[,\n;]+")


class ModerationError(Exception):
    """Erreur métier modération (transition invalide, données manquantes)."""


def get_banned_words() -> set[str]:
    """Ensemble des termes interdits (minuscules). Lu à la connexion chat."""
    return set(BannedWord.objects.values_list("word", flat=True))


def import_banned_words(text: str, created_by=None) -> dict:
    """Importe une liste de mots (séparés par virgule / point-virgule / retour ligne).

    Idempotent : ignore les doublons. Retourne {added, skipped}.
    """
    candidates = {w.strip().lower() for w in _SPLIT_RE.split(text or "") if w.strip()}
    if not candidates:
        return {"added": 0, "skipped": 0}
    existing = set(BannedWord.objects.values_list("word", flat=True))
    to_add = candidates - existing
    BannedWord.objects.bulk_create(
        [BannedWord(word=w, created_by=created_by) for w in sorted(to_add)],
        ignore_conflicts=True,
    )
    return {"added": len(to_add), "skipped": len(candidates) - len(to_add)}


def contains_banned_word(text: str, banned: set[str]) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in banned)


def create_report(
    reporter,
    reason: str,
    target_username: str = "",
    channel_slug: str = "",
    message_id: str = "",
    details: str = "",
) -> Report:
    from accounts.models import User
    from channels_app.models import Channel

    target_user = None
    if target_username:
        target_user = User.objects.filter(username=target_username.lower()).first()
    channel = None
    if channel_slug:
        channel = Channel.objects.filter(slug=channel_slug.lower()).first()
    return Report.objects.create(
        reporter=reporter,
        target_user=target_user,
        channel=channel,
        message_id=message_id,
        reason=reason,
        details=details,
    )


_VALID_STATUS = {s.value for s in Report.Status}


def update_report(
    report: Report,
    moderator,
    status: str = "",
    resolution: str = "",
    assign_to_self: bool = False,
) -> Report:
    """Met à jour le statut / la résolution d'un signalement (action modérateur)."""
    fields: list[str] = []
    if status:
        if status not in _VALID_STATUS:
            raise ModerationError("Statut invalide.")
        report.status = status
        report.reviewed_by = moderator
        fields += ["status", "reviewed_by"]
        if status in (Report.Status.ACTIONED, Report.Status.DISMISSED):
            report.resolved_at = timezone.now()
            fields.append("resolved_at")
    if resolution:
        report.resolution = resolution[:1000]
        fields.append("resolution")
    if assign_to_self:
        report.assigned_to = moderator
        fields.append("assigned_to")
    if fields:
        report.save(update_fields=list(set(fields)))
    return report


def ban_from_report(report: Report, moderator, until=None, reason: str = "") -> None:
    """Bannit l'utilisateur signalé sur la chaîne concernée (réutilise chat.ChatBan)."""
    from chat.models import ChatBan

    if report.channel_id is None or report.target_user_id is None:
        raise ModerationError("Signalement sans chaîne ou utilisateur cible.")
    ChatBan.objects.update_or_create(
        channel=report.channel,
        user=report.target_user,
        defaults={"until": until, "reason": reason or "Signalement", "created_by": moderator},
    )
    update_report(report, moderator, status=Report.Status.ACTIONED)
