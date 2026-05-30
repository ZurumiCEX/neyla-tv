"""Endpoints abonnements : palier (public + config streamer), souscription."""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from channels_app.models import Channel

from . import services
from .models import Subscription
from .serializers import (
    GiftedSubscriptionSerializer,
    MySubscriptionSerializer,
    SubTierSerializer,
    TierWriteSerializer,
)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def channel_tier(request: Request, slug: str) -> Response:  # noqa: ARG001
    channel = Channel.objects.filter(slug=slug.lower()).first()
    tier = services.active_tier(channel) if channel else None
    return Response(SubTierSerializer(tier).data if tier else {"tier": None})


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def my_tier(request: Request) -> Response:
    channel, _ = Channel.objects.get_or_create(
        user=request.user, defaults={"slug": request.user.username}
    )
    if request.method == "GET":
        tier = services.active_tier(channel)
        return Response(SubTierSerializer(tier).data if tier else {"tier": None})
    serializer = TierWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    tier = services.set_tier(channel, data["price_aura"], data["perks"], data["is_active"])
    return Response(SubTierSerializer(tier).data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def subscribe(request: Request) -> Response:
    slug = (request.data.get("channel_slug") or "").strip()
    try:
        sub = services.subscribe(request.user, slug)
    except services.SubscriptionError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:  # InsufficientBalanceError, etc.
        from payments.services import PaymentError

        if isinstance(exc, PaymentError):
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        raise
    return Response(
        {"channel": sub.channel.slug, "current_period_end": sub.current_period_end},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_subscriptions(request: Request) -> Response:
    """Abonnements actifs de l'utilisateur courant (page Suivis)."""
    subs = (
        Subscription.objects.filter(subscriber=request.user, status=Subscription.Status.ACTIVE)
        .select_related("channel__user", "channel__category", "tier")
        .order_by("-created_at")
    )
    return Response({"results": MySubscriptionSerializer(subs, many=True).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def subscription_status(request: Request, slug: str) -> Response:
    channel = Channel.objects.filter(slug=slug.lower()).first()
    subscribed = bool(channel and services.is_subscribed(request.user, channel))
    return Response({"subscribed": subscribed})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def gift(request: Request) -> Response:
    """Offre un abonnement à un autre utilisateur (payé en Aura par l'offreur)."""
    slug = (request.data.get("channel_slug") or request.data.get("channel") or "").strip()
    recipient = (request.data.get("recipient") or "").strip()
    try:
        sub = services.gift_subscription(request.user, slug, recipient)
    except services.SubscriptionError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        from payments.services import PaymentError

        if isinstance(exc, PaymentError):
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        raise
    return Response(
        {
            "channel": sub.channel.slug,
            "recipient": sub.subscriber.username,
            "current_period_end": sub.current_period_end,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_gifts(request: Request) -> Response:
    """Abonnements que j'ai offerts."""
    subs = (
        Subscription.objects.filter(gifted_by=request.user)
        .select_related("channel__user", "channel__category", "tier", "subscriber")
        .order_by("-created_at")
    )
    return Response({"results": GiftedSubscriptionSerializer(subs, many=True).data})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def unsubscribe(request: Request, slug: str) -> Response:
    services.cancel(request.user, slug)
    return Response(status=status.HTTP_204_NO_CONTENT)
