"""Endpoints du dashboard streamer : réglages du chat, mots interdits, journal de
modération, demandes de déban, followers / abonnés."""

from __future__ import annotations

from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Channel

CHAT_FIELDS = (
    "chat_followers_only",
    "chat_follow_min_minutes",
    "chat_subscribers_only",
    "chat_emotes_only",
    "chat_slow_seconds",
    "chat_min_account_age_days",
    "show_viewer_count",
)
# Bornes raisonnables (minutes, secondes, jours).
LIMITS = {
    "chat_follow_min_minutes": 60 * 24 * 90,
    "chat_slow_seconds": 600,
    "chat_min_account_age_days": 365,
}


def _my_channel(user) -> Channel:
    channel, _ = Channel.objects.get_or_create(user=user, defaults={"slug": user.username})
    return channel


def _page(request: Request, default: int = 50) -> tuple[int, int]:
    try:
        limit = max(1, min(int(request.query_params.get("limit", default)), 100))
    except (TypeError, ValueError):
        limit = default
    try:
        offset = max(0, int(request.query_params.get("offset", 0)))
    except (TypeError, ValueError):
        offset = 0
    return limit, offset


def _settings_payload(channel: Channel) -> dict:
    from safety.automod import normalize_settings

    data = {f: getattr(channel, f) for f in CHAT_FIELDS}
    data["automod"] = normalize_settings(channel.automod)
    return data


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="60/m", method="PATCH", block=True)
def chat_settings(request: Request) -> Response:
    """Accès au chat, options et modération automatique de la chaîne."""
    channel = _my_channel(request.user)
    if request.method == "GET":
        return Response(_settings_payload(channel))

    from asgiref.sync import async_to_sync

    from chat.models import ModAction
    from chat.redis_store import set_slowmode
    from safety.automod import normalize_settings

    data = request.data if isinstance(request.data, dict) else {}
    changed = []
    for field in CHAT_FIELDS:
        if field not in data:
            continue
        current = getattr(channel, field)
        if isinstance(current, bool):
            value = bool(data[field])
        else:
            try:
                value = max(0, min(int(data[field]), LIMITS.get(field, 10**6)))
            except (TypeError, ValueError):
                return Response(
                    {"detail": f"Valeur invalide pour {field}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        setattr(channel, field, value)
        changed.append(field)
    if isinstance(data.get("automod"), dict):
        channel.automod = normalize_settings({**(channel.automod or {}), **data["automod"]})
        changed.append("automod")
    if changed:
        channel.save(update_fields=[*changed, "updated_at"])
        if "chat_slow_seconds" in changed:
            # Le slow mode est aussi lu en Redis par le chat (commande /slowmode).
            async_to_sync(set_slowmode)(channel.id, channel.chat_slow_seconds)
        ModAction.objects.create(
            channel=channel,
            actor=request.user,
            action=ModAction.Action.SETTINGS,
            detail=", ".join(changed)[:200],
        )
    return Response(_settings_payload(channel))


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="120/h", method="POST", block=True)
def banned_words(request: Request) -> Response:
    from chat.models import ChannelBannedWord

    channel = _my_channel(request.user)
    if request.method == "POST":
        word = " ".join(str(request.data.get("word") or "").lower().split())[:60]
        if len(word) < 2:
            return Response(
                {"detail": "Mot trop court (2 caractères minimum)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if ChannelBannedWord.objects.filter(channel=channel).count() >= 500:
            return Response(
                {"detail": "Limite de 500 mots atteinte."}, status=status.HTTP_400_BAD_REQUEST
            )
        ChannelBannedWord.objects.get_or_create(channel=channel, word=word)
    words = list(
        ChannelBannedWord.objects.filter(channel=channel).values("id", "word", "created_at")
    )
    return Response({"results": words})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def banned_word_delete(request: Request, pk: int) -> Response:
    from chat.models import ChannelBannedWord

    ChannelBannedWord.objects.filter(channel=_my_channel(request.user), pk=pk).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def _user_brief(user) -> dict | None:
    if user is None:
        return None
    return {
        "username": user.username,
        "display_name": user.display_name or user.username,
        "avatar_url": user.avatar_url,
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mod_actions(request: Request) -> Response:
    from chat.models import ModAction

    limit, offset = _page(request)
    qs = (
        ModAction.objects.filter(channel=_my_channel(request.user))
        .select_related("actor", "target_user")
        .order_by("-created_at")[offset : offset + limit]
    )
    return Response(
        {
            "results": [
                {
                    "id": a.id,
                    "action": a.action,
                    "actor": _user_brief(a.actor),
                    "target": _user_brief(a.target_user),
                    "duration_s": a.duration_s,
                    "detail": a.detail,
                    "created_at": a.created_at,
                }
                for a in qs
            ]
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def unban_requests(request: Request) -> Response:
    from chat.models import UnbanRequest

    status_filter = request.query_params.get("status", "pending")
    qs = UnbanRequest.objects.filter(channel=_my_channel(request.user)).select_related(
        "user", "decided_by"
    )
    if status_filter in {s.value for s in UnbanRequest.Status}:
        qs = qs.filter(status=status_filter)
    limit, offset = _page(request)
    return Response(
        {
            "results": [
                {
                    "id": r.id,
                    "user": _user_brief(r.user),
                    "message": r.message,
                    "status": r.status,
                    "decided_by": _user_brief(r.decided_by),
                    "decided_at": r.decided_at,
                    "created_at": r.created_at,
                }
                for r in qs[offset : offset + limit]
            ]
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unban_request_decide(request: Request, pk: int) -> Response:
    """Accepte (lève le ban) ou refuse une demande de déban."""
    from chat.models import ChatBan, ModAction, UnbanRequest

    channel = _my_channel(request.user)
    req = UnbanRequest.objects.filter(channel=channel, pk=pk).first()
    if req is None:
        return Response({"detail": "Demande introuvable."}, status=status.HTTP_404_NOT_FOUND)
    decision = request.data.get("decision")
    if decision not in ("approve", "deny"):
        return Response(
            {"detail": "decision : approve ou deny."}, status=status.HTTP_400_BAD_REQUEST
        )
    if req.status != UnbanRequest.Status.PENDING:
        return Response({"detail": "Demande déjà traitée."}, status=status.HTTP_409_CONFLICT)
    req.status = (
        UnbanRequest.Status.APPROVED if decision == "approve" else UnbanRequest.Status.DENIED
    )
    req.decided_by = request.user
    req.decided_at = timezone.now()
    req.save(update_fields=["status", "decided_by", "decided_at"])
    if decision == "approve":
        ChatBan.objects.filter(channel=channel, user=req.user).delete()
        ModAction.objects.create(
            channel=channel,
            actor=request.user,
            target_user=req.user,
            action=ModAction.Action.UNBAN,
            detail="demande de déban acceptée",
        )
    return Response({"id": req.id, "status": req.status})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_followers(request: Request) -> Response:
    from social.models import Follow

    limit, offset = _page(request)
    qs = Follow.objects.filter(followee=request.user).select_related("follower")
    rows = qs.order_by("-created_at")[offset : offset + limit]
    return Response(
        {
            "count": qs.count(),
            "results": [{**_user_brief(f.follower), "since": f.created_at} for f in rows],
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_subscribers(request: Request) -> Response:
    from subscriptions.models import Subscription

    limit, offset = _page(request)
    qs = Subscription.objects.filter(
        channel=_my_channel(request.user),
        status=Subscription.Status.ACTIVE,
        current_period_end__gt=timezone.now(),
    ).select_related("subscriber", "gifted_by")
    rows = qs.order_by("-created_at")[offset : offset + limit]
    return Response(
        {
            "count": qs.count(),
            "results": [
                {
                    **_user_brief(s.subscriber),
                    "since": s.created_at,
                    "until": s.current_period_end,
                    "gifted_by": s.gifted_by.username if s.gifted_by else None,
                }
                for s in rows
            ],
        }
    )
