"""Services métier du follow/unfollow."""

from __future__ import annotations

from accounts.models import User

from .models import Follow


class FollowError(Exception):
    """Auto-follow, utilisateur introuvable, etc."""


def follow_user(follower: User, target_username: str) -> Follow:
    target = User.objects.filter(username=target_username.lower()).first()
    if target is None:
        raise FollowError("Utilisateur introuvable.")
    if target.pk == follower.pk:
        raise FollowError("Tu ne peux pas te suivre toi-même.")
    follow, _created = Follow.objects.get_or_create(follower=follower, followee=target)
    return follow


def unfollow_user(follower: User, target_username: str) -> int:
    target = User.objects.filter(username=target_username.lower()).first()
    if target is None:
        raise FollowError("Utilisateur introuvable.")
    deleted, _ = Follow.objects.filter(follower=follower, followee=target).delete()
    return deleted


def is_following(follower: User, target_username: str) -> bool:
    return Follow.objects.filter(
        follower=follower, followee__username=target_username.lower()
    ).exists()
