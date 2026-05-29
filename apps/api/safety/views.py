"""Endpoints admin/modération : événements de risque + flags de contenu."""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.permissions import IsModerator

from . import services
from .models import ContentFlag, RiskEvent
from .serializers import ContentFlagSerializer, RiskEventSerializer


@api_view(["GET"])
@permission_classes([IsModerator])
def risk_events(request: Request) -> Response:
    qs = RiskEvent.objects.select_related("user")
    if request.query_params.get("unresolved") == "1":
        qs = qs.filter(resolved=False)
    kind = request.query_params.get("kind")
    if kind:
        qs = qs.filter(kind=kind)
    return Response({"results": RiskEventSerializer(qs[:200], many=True).data})


@api_view(["POST"])
@permission_classes([IsModerator])
def resolve_risk(request: Request, pk: int) -> Response:
    ev = RiskEvent.objects.filter(pk=pk).first()
    if ev is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    ev.resolved = True
    ev.save(update_fields=["resolved"])
    return Response({"resolved": True})


@api_view(["GET"])
@permission_classes([IsModerator])
def content_flags(request: Request) -> Response:
    qs = ContentFlag.objects.select_related("user", "channel")
    status_filter = request.query_params.get("status")
    if status_filter:
        qs = qs.filter(status=status_filter)
    category = request.query_params.get("category")
    if category:
        qs = qs.filter(category=category)
    return Response({"results": ContentFlagSerializer(qs[:200], many=True).data})


@api_view(["POST"])
@permission_classes([IsModerator])
def resolve_flag(request: Request, pk: int) -> Response:
    flag = ContentFlag.objects.filter(pk=pk).first()
    if flag is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    approve = request.data.get("action") == "approve"
    services.resolve_flag(flag, request.user, approve)
    return Response(ContentFlagSerializer(flag).data)


@api_view(["GET"])
@permission_classes([IsModerator])
def overview(request: Request) -> Response:  # noqa: ARG001
    return Response(
        {
            "open_risk_events": RiskEvent.objects.filter(resolved=False).count(),
            "pending_flags": ContentFlag.objects.filter(status=ContentFlag.Status.PENDING).count(),
            "auto_blocked": ContentFlag.objects.filter(
                status=ContentFlag.Status.AUTO_BLOCKED
            ).count(),
        }
    )
