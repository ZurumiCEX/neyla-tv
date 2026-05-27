"""Endpoints notifications : liste + compteur non lus, marquage lu."""

from __future__ import annotations

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from . import services
from .models import Notification
from .serializers import NotificationSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_notifications(request: Request) -> Response:
    qs = Notification.objects.filter(recipient=request.user)[:50]
    unread = Notification.objects.filter(recipient=request.user, read_at__isnull=True).count()
    return Response({"results": NotificationSerializer(qs, many=True).data, "unread": unread})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_read(request: Request) -> Response:
    ids = request.data.get("ids")
    count = services.mark_read(request.user, ids if isinstance(ids, list) else None)
    return Response({"marked": count})
