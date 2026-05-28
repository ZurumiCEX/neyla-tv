"""Endpoints monétisation : wallet, achat, webhook, tip, payout."""

from __future__ import annotations

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from . import services
from .models import LedgerEntry, Purchase
from .providers import get_provider
from .serializers import (
    LedgerEntrySerializer,
    PayoutSerializer,
    PurchaseSerializer,
    TipSerializer,
    WalletSerializer,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def wallet(request: Request) -> Response:
    return Response(WalletSerializer(services.get_wallet(request.user)).data)


class LedgerHistoryView(ListAPIView):
    """Historique paginé du grand livre de l'utilisateur courant."""

    serializer_class = LedgerEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LedgerEntry.objects.filter(wallet__user=self.request.user)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="30/h", method="POST", block=True)
def purchase(request: Request) -> Response:
    serializer = PurchaseSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    obj, result = services.create_purchase(
        request.user,
        serializer.validated_data["credits"],
        idempotency_key=request.headers.get("Idempotency-Key") or None,
    )
    from . import conversion

    return Response(
        {
            "status": obj.status,
            "checkout_url": result.get("checkout_url"),
            "credits": obj.credits,
            "fiat_amount": str(obj.fiat_amount),
            "currency": obj.currency,
            "equivalents": conversion.equivalents(obj.fiat_amount),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="60/h", method="POST", block=True)
def tip(request: Request) -> Response:
    serializer = TipSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    try:
        result = services.send_tip(
            request.user,
            data["channel_slug"],
            data["aura_amount"],
            data["message"],
            idempotency_key=request.headers.get("Idempotency-Key") or None,
        )
    except services.PaymentError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(
        {"aura_amount": result.aura_amount, "creator_share": result.creator_share},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def payout(request: Request) -> Response:
    serializer = PayoutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        obj = services.request_payout(
            request.user,
            serializer.validated_data["aura_amount"],
            idempotency_key=request.headers.get("Idempotency-Key") or None,
        )
    except services.PaymentError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(
        {"aura_amount": obj.aura_amount, "fiat_amount": str(obj.fiat_amount), "status": obj.status},
        status=status.HTTP_201_CREATED,
    )


@csrf_exempt
@require_POST
def webhook(request, provider: str) -> HttpResponse:
    event = get_provider(provider).verify_webhook(request)
    if not event or not event.get("purchase_id"):
        return JsonResponse({"detail": "Webhook invalide."}, status=400)
    obj = Purchase.objects.filter(id=event["purchase_id"]).first()
    if obj is not None:
        services.confirm_purchase(obj)
    return JsonResponse({"detail": "ok"})
