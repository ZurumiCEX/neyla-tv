"""Endpoints notifications : liste, marquage lu, préférences, messagerie support."""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.permissions import IsSupport

from . import services
from .models import Notification
from .serializers import NotificationSerializer, SupportMessageSerializer


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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_one_read(request: Request, pk: int) -> Response:
    count = services.mark_read(request.user, [pk])
    return Response({"marked": count})


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def preferences(request: Request) -> Response:
    if request.method == "GET":
        return Response(services.get_preferences(request.user))
    mapping = request.data if isinstance(request.data, dict) else {}
    return Response(services.set_preferences(request.user, mapping))


@api_view(["POST"])
@permission_classes([IsSupport])
def support_message(request: Request) -> Response:
    serializer = SupportMessageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    from accounts.models import User

    data = serializer.validated_data
    recipient = User.objects.filter(username=data["username"].lower()).first()
    if recipient is None:
        return Response({"detail": "Destinataire introuvable."}, status=status.HTTP_404_NOT_FOUND)
    services.send_support_message(recipient, data["title"], data["body"], sender=request.user)
    return Response({"detail": "Message envoyé."}, status=status.HTTP_201_CREATED)
