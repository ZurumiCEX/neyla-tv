"""Services modération : mots interdits + création de signalements."""

from __future__ import annotations

from .models import BannedWord, Report


def get_banned_words() -> set[str]:
    """Ensemble des termes interdits (minuscules). Lu à la connexion chat."""
    return set(BannedWord.objects.values_list("word", flat=True))


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
