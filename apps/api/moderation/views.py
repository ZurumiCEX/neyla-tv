"""Endpoint de signalement."""

from __future__ import annotations

from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from . import services
from .serializers import ReportCreateSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="20/h", method="POST", block=True)
def create_report(request: Request) -> Response:
    serializer = ReportCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    services.create_report(
        reporter=request.user,
        reason=data["reason"],
        target_username=data["target_username"],
        channel_slug=data["channel_slug"],
        message_id=data["message_id"],
        details=data["details"],
    )
    return Response({"detail": "Signalement enregistré."}, status=status.HTTP_201_CREATED)
