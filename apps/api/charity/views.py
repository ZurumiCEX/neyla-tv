"""Endpoints Charity (publics + donation authentifiée)."""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from . import services
from .models import Charity, CharityEvent, PlatformEvent
from .serializers import (
    CharityEventSerializer,
    CharitySerializer,
    DonateWriteSerializer,
    PlatformEventSerializer,
)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def list_events(request: Request) -> Response:
    """Calendrier des Charity Days publiés (récents + à venir)."""
    qs = CharityEvent.objects.filter(is_published=True).prefetch_related("beneficiaries")
    return Response({"results": CharityEventSerializer(qs, many=True).data})


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def event_detail(request: Request, slug: str) -> Response:
    event = (
        CharityEvent.objects.filter(slug=slug.lower(), is_published=True)
        .prefetch_related("beneficiaries")
        .first()
    )
    if event is None:
        return Response({"detail": "Événement introuvable."}, status=status.HTTP_404_NOT_FOUND)
    return Response(
        {
            "event": CharityEventSerializer(event).data,
            **services.aggregates(event),
        }
    )


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def current_event(request: Request) -> Response:
    """Raccourci home : événement en cours (ou prochain à défaut)."""
    event = services.current_event() or services.next_event()
    if event is None:
        return Response({"event": None})
    payload = {
        "event": CharityEventSerializer(event).data,
        **services.aggregates(event),
    }
    return Response(payload)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def list_charities(request: Request) -> Response:
    qs = Charity.objects.filter(is_active=True)
    return Response({"results": CharitySerializer(qs, many=True).data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def donate(request: Request) -> Response:
    serializer = DonateWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    try:
        donation = services.donate(
            request.user,
            data["event_slug"],
            data["charity_slug"],
            data["aura_amount"],
            data.get("message", ""),
            data.get("anonymous", False),
        )
    except services.CharityError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        from payments.services import PaymentError

        if isinstance(exc, PaymentError):
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        raise
    return Response(
        {
            "event": donation.event.slug,
            "charity": donation.charity.slug,
            "aura_amount": donation.aura_amount,
            "created_at": donation.created_at,
        },
        status=status.HTTP_201_CREATED,
    )


# --- Calendrier d'événements de plateforme (header menu + page calendrier) ---


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def list_platform_events(request: Request) -> Response:
    """Liste publiée, filtrable par `kind` et plage de dates `from`/`to`."""
    qs = PlatformEvent.objects.filter(is_published=True)
    kind = (request.query_params.get("kind") or "").strip().lower()
    if kind:
        qs = qs.filter(kind=kind)
    from datetime import datetime

    def _parse(s: str | None):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None

    dt_from = _parse(request.query_params.get("from"))
    dt_to = _parse(request.query_params.get("to"))
    if dt_from is not None:
        qs = qs.filter(ends_at__gte=dt_from)
    if dt_to is not None:
        qs = qs.filter(starts_at__lte=dt_to)
    return Response({"results": PlatformEventSerializer(qs, many=True).data})


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def list_upcoming_platform_events(request: Request) -> Response:
    """Raccourci header : N prochains événements (par défaut 5)."""
    from django.utils import timezone

    try:
        limit = max(1, min(int(request.query_params.get("limit") or 5), 20))
    except (TypeError, ValueError):
        limit = 5
    now = timezone.now()
    qs = PlatformEvent.objects.filter(is_published=True, ends_at__gte=now).order_by(
        "-featured", "starts_at"
    )[:limit]
    return Response({"results": PlatformEventSerializer(qs, many=True).data})


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def platform_event_detail(request: Request, slug: str) -> Response:
    ev = PlatformEvent.objects.filter(slug=slug.lower(), is_published=True).first()
    if ev is None:
        return Response({"detail": "Événement introuvable."}, status=status.HTTP_404_NOT_FOUND)
    return Response(PlatformEventSerializer(ev).data)
