"""Helpers de test : chaîne de streamer approuvé (provisionnée en mode FAKE)."""

from __future__ import annotations


def provisioned_channel(user):
    """Chaîne de `user`, provisionnée (streamer approuvé) — seule une chaîne
    provisionnée peut recevoir tips et abonnements."""
    from .models import Channel
    from .services import provision_channel

    channel = Channel.objects.get(user=user)
    provision_channel(channel)
    channel.refresh_from_db()
    return channel
