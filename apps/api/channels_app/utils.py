"""Helpers transverses du domaine chaînes."""

from __future__ import annotations


def is_streamer(user) -> bool:
    """Vrai si l'utilisateur possède une chaîne provisionnée (streamer approuvé).

    Lecture fraîche en base : n'utilise pas le cache de la relation OneToOne
    `user.channel`, qui peut être périmé dans les flux longs (webhooks, tâches).
    """
    if user is None or not getattr(user, "pk", None):
        return False
    from .models import Channel

    return Channel.objects.filter(user_id=user.pk).exclude(stream_id="").exists()
