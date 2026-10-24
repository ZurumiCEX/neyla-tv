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
from .models import LedgerEntry, Payout, Purchase
from .providers import get_provider, is_known_provider
from .serializers import (
    LedgerEntrySerializer,
    PayoutHistorySerializer,
    PurchaseHistorySerializer,
    PurchaseSerializer,
    TipSerializer,
    WalletSerializer,
    WithdrawalConfirmSerializer,
    WithdrawalQuoteSerializer,
    WithdrawalStartSerializer,
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


class PurchaseHistoryView(ListAPIView):
    """Historique paginé des achats fiat (packs d'Aura) de l'utilisateur courant."""

    serializer_class = PurchaseHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Purchase.objects.filter(user=self.request.user)


class PayoutHistoryView(ListAPIView):
    """Historique paginé des retraits de l'utilisateur courant."""

    serializer_class = PayoutHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payout.objects.filter(user=self.request.user)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def purchase_detail(request: Request, pk: int) -> Response:
    """Statut d'un achat (suivi après retour du checkout Stripe)."""
    obj = Purchase.objects.filter(pk=pk, user=request.user).first()
    if obj is None:
        return Response({"detail": "Achat introuvable."}, status=status.HTTP_404_NOT_FOUND)
    return Response(PurchaseHistorySerializer(obj).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="30/h", method="POST", block=True)
def purchase(request: Request) -> Response:
    serializer = PurchaseSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        obj, result = services.create_purchase(
            request.user,
            serializer.validated_data["credits"],
            idempotency_key=request.headers.get("Idempotency-Key") or None,
            method=serializer.validated_data.get("method", "card"),
        )
    except services.PaymentError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    from . import conversion

    return Response(
        {
            "id": obj.id,
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def withdrawal_eligibility(request: Request) -> Response:
    """État d'éligibilité au retrait + solde retirable + frais."""
    wallet = services.get_wallet(request.user)
    return Response(
        {
            "is_streamer": services.is_eligible_streamer(request.user),
            "balance": wallet.aura_balance,
            "withdrawable": services.withdrawable_balance(request.user),
            "fee_pct": float(round(services.withdrawal_fee_pct() * 100, 2)),
            "min_aura": services.withdrawal_min_aura(),
            "payout_hold": wallet.payout_hold,
            "unit_price_xof": str(services.aura_unit_price()),
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="10/h", method="POST", block=True)
def withdrawal_quote(request: Request) -> Response:
    serializer = WithdrawalQuoteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(services.withdrawal_quote(serializer.validated_data["aura_amount"]))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="10/h", method="POST", block=True)
def withdrawal_start(request: Request) -> Response:
    serializer = WithdrawalStartSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        data = serializer.validated_data
        services.start_withdrawal(
            request.user,
            data["aura_amount"],
            data["destination_provider"],
            data["destination_phone"],
        )
    except services.PaymentError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"otp_sent": True, "ttl_minutes": services.WITHDRAWAL_OTP_TTL_MIN})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="15/h", method="POST", block=True)
def withdrawal_confirm(request: Request) -> Response:
    serializer = WithdrawalConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    from accounts import two_factor

    if two_factor.is_enabled(request.user) and not two_factor.verify(
        request.user, str(request.data.get("totp") or "")
    ):
        return Response(
            {"detail": "Code de double authentification requis ou invalide.", "code": "totp"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        obj = services.confirm_withdrawal(request.user, serializer.validated_data["code"])
    except services.PaymentError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(PayoutHistorySerializer(obj).data, status=status.HTTP_201_CREATED)


@csrf_exempt
@require_POST
def webhook(request, provider: str) -> HttpResponse:
    if not is_known_provider(provider):
        return JsonResponse({"detail": "Fournisseur inconnu."}, status=404)
    event = get_provider(provider).verify_webhook(request)
    if not event:
        return JsonResponse({"detail": "Webhook invalide."}, status=400)
    services.handle_provider_event(provider, event)
    return JsonResponse({"detail": "ok"})
