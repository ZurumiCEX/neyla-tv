"""Endpoints modération : signalement (public auth) + file de traitement (modérateur)."""

from __future__ import annotations

from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.permissions import IsModerator

from . import services
from .models import Report
from .serializers import (
    BannedWordImportSerializer,
    ReportCreateSerializer,
    ReportSerializer,
    ReportUpdateSerializer,
)


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


class ReportListView(ListAPIView):
    """File des signalements (modérateur), filtrable par statut."""

    serializer_class = ReportSerializer
    permission_classes = [IsModerator]

    def get_queryset(self):
        qs = Report.objects.select_related(
            "reporter", "target_user", "channel", "assigned_to"
        ).all()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


@api_view(["PATCH"])
@permission_classes([IsModerator])
def report_detail(request: Request, pk: int) -> Response:
    report = Report.objects.filter(pk=pk).first()
    if report is None:
        return Response({"detail": "Signalement introuvable."}, status=status.HTTP_404_NOT_FOUND)
    serializer = ReportUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    try:
        if data["ban"]:
            services.ban_from_report(report, request.user, reason="Signalement traité")
        services.update_report(
            report,
            request.user,
            status=data["status"],
            resolution=data["resolution"],
            assign_to_self=data["assign_to_self"],
        )
    except services.ModerationError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    report.refresh_from_db()
    return Response(ReportSerializer(report).data)


@api_view(["POST"])
@permission_classes([IsModerator])
def import_banned_words(request: Request) -> Response:
    uploaded = request.FILES.get("file")
    if uploaded is not None:
        words = uploaded.read().decode("utf-8", errors="ignore")
    else:
        serializer = BannedWordImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        words = serializer.validated_data["words"]
    result = services.import_banned_words(words, created_by=request.user)
    return Response(result, status=status.HTTP_201_CREATED)
