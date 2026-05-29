"""Endpoints invitations : génération + liste de mes codes (avec compteur de succès)."""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from . import services
from .models import Invite
from .serializers import InviteCreateSerializer, InviteSerializer


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def invites(request: Request) -> Response:
    if request.method == "POST":
        serializer = InviteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invite = services.create_invite(request.user, serializer.validated_data["max_uses"])
        return Response(InviteSerializer(invite).data, status=status.HTTP_201_CREATED)
    qs = Invite.objects.filter(inviter=request.user)
    return Response(
        {
            "results": InviteSerializer(qs, many=True).data,
            "successful_invites": services.successful_count(request.user),
            "referral": services.referral_stats(request.user),
        }
    )
