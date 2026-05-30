"""Endpoints analytics : résumé streamer + vue d'ensemble admin."""

from __future__ import annotations

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.permissions import IsAdminRole

from . import services


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_analytics(request: Request) -> Response:
    return Response(services.my_analytics(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_revenue(request: Request) -> Response:
    """Revenus consolidés (tips + abonnements + parrainage) du créateur connecté."""
    period = (request.query_params.get("period") or "day").strip().lower()
    return Response(services.creator_revenue(request.user, period=period))


@api_view(["GET"])
@permission_classes([IsAdminRole])
def overview(request: Request) -> Response:  # noqa: ARG001
    return Response(services.platform_overview())


@api_view(["GET"])
@permission_classes([IsAdminRole])
def dashboard(request: Request) -> Response:
    days = int(request.query_params.get("days") or 14)
    return Response(services.admin_dashboard(days))


@api_view(["GET"])
@permission_classes([IsAdminRole])
def monitoring(request: Request) -> Response:  # noqa: ARG001
    return Response(services.monitoring())
