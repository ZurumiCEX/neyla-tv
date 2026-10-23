"""Endpoints REST pour les chaînes."""

from __future__ import annotations

import logging

from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Channel
from .serializers import (
    MyChannelSerializer,
    PublicChannelSerializer,
    StreamSessionSerializer,
)
from .services import mark_live, mark_offline, rotate_stream_key

logger = logging.getLogger(__name__)


def _get_my_channel(user) -> Channel:
    """Récupère la chaîne de l'utilisateur (créée à l'inscription, non provisionnée).

    Le provisioning n'a lieu qu'à l'approbation streamer — pas ici.
    """
    channel, _ = Channel.objects.get_or_create(user=user, defaults={"slug": user.username})
    return channel


def _ensure_overlay_token(channel: Channel) -> Channel:
    if not channel.overlay_token:
        import secrets

        channel.overlay_token = secrets.token_urlsafe(24)
        channel.save(update_fields=["overlay_token", "updated_at"])
    return channel


def _reconcile_provisioning(channel: Channel, user) -> None:
    """Auto-répare : un streamer approuvé dont la chaîne n'est pas provisionnée
    (approbation hors flux normal, worker indisponible…) est provisionné ici."""
    if channel.is_provisioned:
        return
    try:
        from streamers.models import StreamerApplication

        approved = StreamerApplication.objects.filter(
            user=user, status=StreamerApplication.Status.APPROVED
        ).exists()
        if not approved:
            return
        from .services import provision_channel

        provision_channel(channel)
        channel.refresh_from_db()
    except Exception:  # noqa: BLE001 — best-effort, ne bloque jamais le dashboard
        logger.exception("reconcile provisioning failed for user %s", user.pk)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def my_channel(request: Request) -> Response:
    channel = _get_my_channel(request.user)
    if request.method == "GET":
        from chat.redis_store import get_viewers_count
        from social.models import Follow

        _reconcile_provisioning(channel, request.user)
        _ensure_overlay_token(channel)
        data = MyChannelSerializer(channel).data
        data["follower_count"] = Follow.objects.filter(followee=request.user).count()
        data["viewers"] = get_viewers_count(channel.id)
        return Response(data)
    serializer = MyChannelSerializer(channel, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    _scan_channel_text(channel)
    return Response(serializer.data)


def _scan_channel_text(channel) -> None:
    """Analyse anti-violation du titre + tags (best-effort)."""
    try:
        from safety.services import scan_text

        scan_text(channel.title, "title", channel=channel)
        for tag in channel.tags or []:
            scan_text(tag, "tag", channel=channel)
    except Exception:  # noqa: BLE001
        logger.debug("channel text scan failed", exc_info=True)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_sessions(request: Request) -> Response:
    """Historique des sessions de diffusion du propriétaire (les plus récentes)."""
    channel = _get_my_channel(request.user)
    try:
        limit = min(int(request.query_params.get("limit", 50)), 100)
    except (TypeError, ValueError):
        limit = 50
    sessions = channel.sessions.all()[:limit]
    return Response({"results": StreamSessionSerializer(sessions, many=True).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_activity(request: Request) -> Response:
    """Fil d'activité récent du streamer : nouveaux followers, tips, abonnements."""
    from payments.models import Tip
    from social.models import Follow
    from subscriptions.models import Subscription

    channel = _get_my_channel(request.user)
    try:
        limit = min(int(request.query_params.get("limit", 30)), 100)
    except (TypeError, ValueError):
        limit = 30

    events: list[dict] = []
    for f in (
        Follow.objects.filter(followee=request.user)
        .select_related("follower")
        .order_by("-created_at")[:limit]
    ):
        events.append(
            {
                "type": "follow",
                "actor": f.follower.display_name or f.follower.username,
                "created_at": f.created_at,
            }
        )
    for tp in (
        Tip.objects.filter(to_channel=channel)
        .select_related("from_user")
        .order_by("-created_at")[:limit]
    ):
        events.append(
            {
                "type": "tip",
                "actor": tp.from_user.display_name or tp.from_user.username,
                "amount": tp.aura_amount,
                "message": tp.message,
                "created_at": tp.created_at,
            }
        )
    for sub in (
        Subscription.objects.filter(channel=channel)
        .select_related("subscriber")
        .order_by("-created_at")[:limit]
    ):
        events.append(
            {
                "type": "subscribe",
                "actor": sub.subscriber.display_name or sub.subscriber.username,
                "created_at": sub.created_at,
            }
        )

    events.sort(key=lambda e: e["created_at"], reverse=True)
    return Response({"results": events[:limit]})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def overlay_token(request: Request) -> Response:
    """(Re)génère le jeton secret de l'overlay d'alertes."""
    import secrets

    channel = _get_my_channel(request.user)
    channel.overlay_token = secrets.token_urlsafe(24)
    channel.save(update_fields=["overlay_token", "updated_at"])
    return Response({"overlay_token": channel.overlay_token})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="30/h", method="POST", block=True)
def overlay_test(request: Request) -> Response:
    """Envoie une alerte de test à l'overlay du streamer."""
    from .alerts import send_overlay_alert

    channel = _ensure_overlay_token(_get_my_channel(request.user))
    kind = request.data.get("kind") or "follow"
    if kind not in ("follow", "tip", "subscribe"):
        kind = "follow"
    name = request.user.display_name or request.user.username
    send_overlay_alert(channel.id, kind, actor=name, amount=100 if kind == "tip" else None)
    return Response({"sent": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="60/h", method="POST", block=True)
def set_live(request: Request) -> Response:
    """Bascule live manuelle (repli/démo quand le polling Bunny n'a pas encore vu le flux).

    Réservée aux chaînes provisionnées (streamer approuvé) : sinon n'importe quel
    compte pourrait notifier ses followers et ouvrir des sessions fictives.
    """
    channel = _get_my_channel(request.user)
    going_live = bool(request.data.get("live", True))
    if going_live and not channel.is_provisioned:
        raise PermissionDenied(
            "Chaîne non provisionnée : l'accès streamer doit d'abord être approuvé."
        )
    if going_live:
        changed = mark_live(channel)
        if changed:
            from notifications.services import notify_followers_live

            notify_followers_live(channel)
    else:
        changed = mark_offline(channel)
    return Response({"is_live": channel.is_live, "changed": changed})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="5/d", method="POST", block=True)
def rotate_key(request: Request) -> Response:  # noqa: ARG001
    channel = _get_my_channel(request.user)
    if not channel.is_provisioned:
        raise PermissionDenied(
            "Chaîne non provisionnée : l'accès streamer doit d'abord être approuvé."
        )
    rotate_stream_key(channel)
    channel.refresh_from_db()
    return Response(MyChannelSerializer(channel).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="30/m", method="GET", block=True)
def stream_health(request: Request) -> Response:
    """État du flux côté Bunny (« Tester la connexion » du dashboard)."""
    from .bunny import BunnyStreamError, get_client
    from .tasks import sync_channel_status

    channel = _get_my_channel(request.user)
    if not channel.is_provisioned:
        raise PermissionDenied(
            "Chaîne non provisionnée : l'accès streamer doit d'abord être approuvé."
        )
    client = get_client()
    payload = {
        "provider": "bunny",
        "mode": "fake" if client.is_fake else "live",
        "is_live": channel.is_live,
        "reachable": True,
        "checked_at": channel.stream_checked_at,
    }
    if not client.is_fake:
        try:
            state = sync_channel_status(channel, client)
        except BunnyStreamError:
            state = None
        channel.refresh_from_db()
        payload.update(
            {
                "reachable": state is not None,
                "is_live": channel.is_live,
                "checked_at": channel.stream_checked_at,
            }
        )
    return Response(payload)


def goal_progress(channel: Channel) -> int:
    """Progression de l'objectif depuis son lancement (abonnés ou Aura reçue)."""
    since = channel.goal_started_at or channel.created_at
    if channel.goal_kind == "tips":
        from django.db.models import Sum

        from payments.models import Tip

        return int(
            Tip.objects.filter(to_channel=channel, created_at__gte=since).aggregate(
                s=Sum("aura_amount")
            )["s"]
            or 0
        )
    from subscriptions.models import Subscription

    return Subscription.objects.filter(channel=channel, started_at__gte=since).count()


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@ratelimit(key="ip", rate="120/m", method="GET", block=True)
def overlay_info(request: Request, token: str) -> Response:  # noqa: ARG001
    """Données des widgets OBS (chat, objectif) : authentifié par le jeton overlay."""
    channel = Channel.objects.filter(overlay_token=token).first() if token else None
    if channel is None:
        raise NotFound("Overlay introuvable.")
    goal = None
    if channel.goal_target > 0:
        goal = {
            "title": channel.goal_title,
            "kind": channel.goal_kind,
            "target": channel.goal_target,
            "current": goal_progress(channel),
        }
    response = Response({"slug": channel.slug, "is_live": channel.is_live, "goal": goal})
    response["Cache-Control"] = "no-store"
    return response


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def public_channel(request: Request, slug: str) -> Response:  # noqa: ARG001
    channel = Channel.objects.select_related("user").filter(slug=slug.lower()).first()
    if channel is None:
        raise NotFound("Chaîne introuvable.")
    from social.models import Follow

    data = PublicChannelSerializer(channel).data
    data["follower_count"] = Follow.objects.filter(followee=channel.user).count()
    data["is_verified"] = channel.is_provisioned
    data["goal"] = (
        {
            "title": channel.goal_title,
            "kind": channel.goal_kind,
            "target": channel.goal_target,
            "current": goal_progress(channel),
        }
        if channel.goal_target > 0
        else None
    )
    return Response(data, status=status.HTTP_200_OK)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def channel_status(request: Request, slug: str) -> Response:  # noqa: ARG001
    """Payload léger pour le badge LIVE + viewers (poll 5s, cacheable côté CDN)."""
    channel = (
        Channel.objects.filter(slug=slug.lower())
        .only("id", "is_live", "last_live_started_at")
        .first()
    )
    if channel is None:
        raise NotFound("Chaîne introuvable.")
    from chat.redis_store import get_viewers_count

    response = Response(
        {
            "is_live": channel.is_live,
            "last_live_started_at": channel.last_live_started_at,
            "viewers": get_viewers_count(channel.id),
        }
    )
    response["Cache-Control"] = "public, max-age=5"
    return response
