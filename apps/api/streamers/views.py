"""Endpoints candidature streamer."""

from __future__ import annotations

from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from . import services
from .models import StreamerApplication
from .serializers import StreamerApplicationSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="3/h", method="POST", block=True)
def submit(request: Request) -> Response:
    motivation = (request.data.get("motivation") or "").strip()
    try:
        application = services.submit_application(request.user, motivation)
    except services.AlreadyStreamerError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
    return Response(
        StreamerApplicationSerializer(application).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_application(request: Request) -> Response:
    application = StreamerApplication.objects.filter(user=request.user).first()
    if application is None:
        return Response({"status": "none"})
    return Response(StreamerApplicationSerializer(application).data)
