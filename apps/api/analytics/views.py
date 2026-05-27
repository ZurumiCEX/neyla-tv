"""Endpoints analytics : résumé streamer + vue d'ensemble admin."""

from __future__ import annotations

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from . import services


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_analytics(request: Request) -> Response:
    return Response(services.my_analytics(request.user))


@api_view(["GET"])
@permission_classes([IsAdminUser])
def overview(request: Request) -> Response:  # noqa: ARG001
    return Response(services.platform_overview())
