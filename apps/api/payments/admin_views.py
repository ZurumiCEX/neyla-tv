"""Endpoints admin revenue : transactions unifiées, règles de commission, retraits."""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.permissions import IsAdminRole

from . import services
from .models import FeeRule, Payout
from .serializers import FeeRuleSerializer


@api_view(["GET"])
@permission_classes([IsAdminRole])
def transactions(request: Request) -> Response:
    rows = services.list_transactions(
        type_filter=request.query_params.get("type", ""),
        query=request.query_params.get("q", ""),
        days=int(request.query_params.get("days") or 0),
    )
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(rows, request)
    return paginator.get_paginated_response(page)


@api_view(["GET", "POST"])
@permission_classes([IsAdminRole])
def fees(request: Request) -> Response:
    if request.method == "GET":
        return Response(FeeRuleSerializer(FeeRule.objects.all(), many=True).data)
    serializer = FeeRuleSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAdminRole])
def fee_detail(request: Request, pk: int) -> Response:
    rule = FeeRule.objects.filter(pk=pk).first()
    if rule is None:
        return Response({"detail": "Règle introuvable."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "DELETE":
        rule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = FeeRuleSerializer(rule, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAdminRole])
def resolve_payout(request: Request, pk: int) -> Response:
    payout = Payout.objects.filter(pk=pk).first()
    if payout is None:
        return Response({"detail": "Retrait introuvable."}, status=status.HTTP_404_NOT_FOUND)
    action = (request.data.get("action") or "").strip()
    try:
        services.resolve_payout(request.user, payout, action)
    except services.PaymentError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"status": payout.status})
