"""Services métier du follow/unfollow."""

from __future__ import annotations

from accounts.models import User

from .models import Collaboration, Follow


class FollowError(Exception):
    """Auto-follow, utilisateur introuvable, etc."""


class CollaborationError(Exception):
    """Invitation invalide (soi-même, introuvable, collaborations fermées…)."""


def follow_user(follower: User, target_username: str) -> Follow:
    target = User.objects.filter(username=target_username.lower()).first()
    if target is None:
        raise FollowError("Utilisateur introuvable.")
    if target.pk == follower.pk:
        raise FollowError("Tu ne peux pas te suivre toi-même.")
    follow, created = Follow.objects.get_or_create(follower=follower, followee=target)
    if created:
        from notifications.models import Notification
        from notifications.services import create_notification

        create_notification(
            recipient=target,
            type=Notification.Type.NEW_FOLLOWER,
            actor=follower,
            payload={"username": follower.username},
        )
        from gamification.services import check_and_award

        check_and_award(target, "follow_received")
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


def invite_collaborator(inviter: User, target_username: str) -> Collaboration:
    """Invite un créateur à collaborer. Réutilise/relance une invitation existante."""
    target = User.objects.filter(username=target_username.lower()).first()
    if target is None:
        raise CollaborationError("Utilisateur introuvable.")
    if target.pk == inviter.pk:
        raise CollaborationError("Tu ne peux pas t'inviter toi-même.")
    # L'invité doit accepter les collaborations sur sa chaîne.
    channel = getattr(target, "channel", None)
    if channel is not None and not channel.collaborations_open:
        raise CollaborationError("Cet utilisateur n'accepte pas les collaborations.")
    # Lien inverse déjà accepté ? On ne duplique pas.
    reverse = Collaboration.objects.filter(inviter=target, invitee=inviter).first()
    if reverse and reverse.status == Collaboration.Status.ACCEPTED:
        return reverse
    collab, created = Collaboration.objects.get_or_create(inviter=inviter, invitee=target)
    if not created and collab.status != Collaboration.Status.ACCEPTED:
        collab.status = Collaboration.Status.PENDING
        collab.responded_at = None
        collab.save(update_fields=["status", "responded_at"])
    if created:
        from notifications.services import send_support_message

        send_support_message(
            target,
            "Invitation à collaborer",
            f"@{inviter.username} t'invite à collaborer.",
            sender=inviter,
        )
    return collab


def respond_collaboration(user: User, collab_id: int, accept: bool) -> Collaboration | None:
    """L'invité accepte ou refuse une invitation le concernant."""
    from django.utils import timezone

    collab = Collaboration.objects.filter(id=collab_id, invitee=user).first()
    if collab is None:
        return None
    collab.status = Collaboration.Status.ACCEPTED if accept else Collaboration.Status.DECLINED
    collab.responded_at = timezone.now()
    collab.save(update_fields=["status", "responded_at"])
    return collab


def remove_collaboration(user: User, collab_id: int) -> int:
    """Supprime une collaboration où l'utilisateur est partie prenante."""
    from django.db.models import Q

    deleted, _ = (
        Collaboration.objects.filter(id=collab_id)
        .filter(Q(inviter=user) | Q(invitee=user))
        .delete()
    )
    return deleted
