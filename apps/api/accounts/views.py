"""Vues d'auth : fines, déléguent au service. Refresh stocké en cookie HttpOnly."""

from __future__ import annotations

import contextlib

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError as DjangoValidationError
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from . import sessions, totp, two_factor
from .models import GuideProgress, User, UserSession
from .serializers import (
    EmailSerializer,
    MeSerializer,
    PasswordResetConfirmSerializer,
    RegisterSerializer,
    TokenSerializer,
    UserSessionSerializer,
)
from .services import (
    RegistrationError,
    register_user,
    reset_password_with_token,
    verify_email_token,
)
from .tasks import send_email_verification, send_password_reset
from .tokens import (
    TWO_FACTOR_PURPOSE,
    TWO_FACTOR_TTL,
    InvalidToken,
    InvalidTokenError,
    make_token,
    read_token,
)

GENERIC_AUTH_ERROR = {"detail": "Identifiants invalides."}
GENERIC_RESET_OK = {"detail": "Si un compte existe, un email a été envoyé."}


def _set_refresh_cookie(response: Response, refresh_token: str) -> Response:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.REFRESH_COOKIE_MAX_AGE,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
    )
    return response


def _clear_refresh_cookie(response: Response) -> Response:
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
    )
    return response


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@ratelimit(key="ip", rate="5/5m", method="POST", block=True)
def register(request: Request) -> Response:
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = dict(serializer.validated_data)
    invite_code = data.pop("invite", "")
    terms_accepted = data.pop("terms_accepted", False)
    try:
        user = register_user(**data, invite_code=invite_code, terms_accepted=terms_accepted)
    except RegistrationError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except DjangoValidationError as exc:
        return Response({"password": list(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)
    send_email_verification.delay(user.pk)
    return Response(MeSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@ratelimit(key="ip", rate="10/5m", method="POST", block=True)
def login(request: Request) -> Response:
    email = (request.data.get("email") or "").strip()
    password = request.data.get("password") or ""
    if not email or not password:
        return Response(GENERIC_AUTH_ERROR, status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(request, email=email, password=password)
    if user is None or not user.is_active:
        return Response(GENERIC_AUTH_ERROR, status=status.HTTP_401_UNAUTHORIZED)

    # 2FA activée : on ne délivre pas de tokens, on demande un second facteur.
    if two_factor.is_enabled(user):
        return Response(
            {
                "two_factor_required": True,
                "token": make_token(user.pk, TWO_FACTOR_PURPOSE),
            },
            status=status.HTTP_200_OK,
        )
    return _issue_session(user, request)


def _issue_session(user, request) -> Response:
    """Délivre access + refresh (cookie) après une authentification réussie."""
    from gamification.services import check_and_award

    check_and_award(user, "first_login")
    refresh = RefreshToken.for_user(user)
    sessions.record_login(user, request, refresh)
    response = Response(
        {"access": str(refresh.access_token), "user": MeSerializer(user).data},
        status=status.HTTP_200_OK,
    )
    return _set_refresh_cookie(response, str(refresh))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@ratelimit(key="ip", rate="10/5m", method="POST", block=True)
def two_factor_login(request: Request) -> Response:
    """Second facteur : valide le token éphémère + le code TOTP/secours."""
    token = request.data.get("token") or ""
    code = request.data.get("code") or ""
    try:
        user_id = read_token(token, TWO_FACTOR_PURPOSE, TWO_FACTOR_TTL)
    except InvalidTokenError:
        return Response(GENERIC_AUTH_ERROR, status=status.HTTP_401_UNAUTHORIZED)
    user = User.objects.filter(pk=user_id, is_active=True).first()
    if user is None or not two_factor.verify(user, code):
        return Response(
            {"detail": "Code de vérification invalide."}, status=status.HTTP_401_UNAUTHORIZED
        )
    return _issue_session(user, request)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def refresh(request: Request) -> Response:
    token = request.COOKIES.get(settings.REFRESH_COOKIE_NAME) or request.data.get("refresh")
    if not token:
        return Response({"detail": "Refresh manquant."}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        old = RefreshToken(token)
        old_jti = old.get("jti")
        old.blacklist()
        user = User.objects.filter(pk=old["user_id"]).first()
        if user is None or not user.is_active:
            raise TokenError("Utilisateur invalide.")
        new = RefreshToken.for_user(user)
    except TokenError:
        response = Response({"detail": "Refresh invalide."}, status=status.HTTP_401_UNAUTHORIZED)
        return _clear_refresh_cookie(response)
    sessions.record_rotation(old_jti, new, request)
    response = Response({"access": str(new.access_token)}, status=status.HTTP_200_OK)
    return _set_refresh_cookie(response, str(new))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def logout(request: Request) -> Response:
    token = request.COOKIES.get(settings.REFRESH_COOKIE_NAME) or request.data.get("refresh")
    if token:
        with contextlib.suppress(TokenError):
            parsed = RefreshToken(token)
            sessions.revoke_jti(parsed.get("jti"))
            parsed.blacklist()
    response = Response(status=status.HTTP_204_NO_CONTENT)
    return _clear_refresh_cookie(response)


def _touch_last_active(user) -> None:
    """Marque l'utilisateur actif (pour DAU/MAU). Écrit au plus une fois / 5 min."""
    from datetime import timedelta

    from django.utils import timezone

    now = timezone.now()
    if user.last_active_at is None or now - user.last_active_at > timedelta(minutes=5):
        user.last_active_at = now
        user.save(update_fields=["last_active_at"])


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request: Request) -> Response:
    if request.method == "GET":
        _touch_last_active(request.user)
        return Response(MeSerializer(request.user).data)
    serializer = MeSerializer(request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


def _active_sessions(user):
    """Sessions non révoquées dont le refresh n'a pas expiré (approché via last_seen)."""
    from django.utils import timezone

    cutoff = timezone.now() - settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
    return UserSession.objects.filter(user=user, revoked=False, last_seen_at__gte=cutoff)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_sessions(request: Request) -> Response:
    cur = sessions.current_jti(request)
    data = []
    for s in _active_sessions(request.user):
        item = UserSessionSerializer(s).data
        item["is_current"] = s.jti == cur
        data.append(item)
    return Response({"results": data})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def revoke_session(request: Request, pk: int) -> Response:
    session = UserSession.objects.filter(pk=pk, user=request.user).first()
    if session is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    sessions.revoke_jti(session.jti)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def revoke_other_sessions(request: Request) -> Response:
    """Déconnecte tous les autres appareils (garde la session courante)."""
    cur = sessions.current_jti(request)
    count = 0
    for s in _active_sessions(request.user).exclude(jti=cur):
        sessions.revoke_jti(s.jti)
        count += 1
    return Response({"revoked": count})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def two_factor_setup(request: Request) -> Response:
    if two_factor.is_enabled(request.user):
        return Response({"detail": "2FA déjà activée."}, status=status.HTTP_400_BAD_REQUEST)
    tf = two_factor.begin_setup(request.user)
    return Response(
        {
            "secret": tf.secret,
            "otpauth_uri": totp.provisioning_uri(tf.secret, request.user.email),
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def two_factor_enable(request: Request) -> Response:
    recovery = two_factor.enable(request.user, (request.data.get("code") or "").strip())
    if recovery is None:
        return Response({"detail": "Code invalide."}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"enabled": True, "recovery_codes": recovery})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def two_factor_disable(request: Request) -> Response:
    if not two_factor.disable(request.user, (request.data.get("code") or "").strip()):
        return Response({"detail": "Code invalide."}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"enabled": False})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def email_verify(request: Request) -> Response:
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        verify_email_token(serializer.validated_data["token"])
    except InvalidToken as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": "Email vérifié."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="3/h", method="POST", block=True)
def email_resend(request: Request) -> Response:
    if not request.user.is_email_verified:
        send_email_verification.delay(request.user.pk)
    return Response({"detail": "Si nécessaire, un email a été renvoyé."})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@ratelimit(key="ip", rate="5/h", method="POST", block=True)
def password_reset_request(request: Request) -> Response:
    serializer = EmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = User.objects.filter(email__iexact=serializer.validated_data["email"]).first()
    if user is not None:
        send_password_reset.delay(user.pk)
    return Response(GENERIC_RESET_OK)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@ratelimit(key="ip", rate="10/h", method="POST", block=True)
def password_reset_confirm(request: Request) -> Response:
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        reset_password_with_token(
            token=serializer.validated_data["token"],
            new_password=serializer.validated_data["password"],
        )
    except InvalidToken as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except DjangoValidationError as exc:
        return Response({"password": list(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": "Mot de passe mis à jour."})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def guide_progress(request: Request) -> Response:
    """Suivi des acquis : liste des cles validees, ou (de)valide une etape."""
    if request.method == "GET":
        keys = list(GuideProgress.objects.filter(user=request.user).values_list("key", flat=True))
        return Response({"completed": keys})
    key = (request.data.get("key") or "").strip()[:120]
    if not key:
        return Response({"detail": "Cle requise."}, status=status.HTTP_400_BAD_REQUEST)
    done = bool(request.data.get("done", True))
    if done:
        GuideProgress.objects.get_or_create(user=request.user, key=key)
    else:
        GuideProgress.objects.filter(user=request.user, key=key).delete()
    keys = list(GuideProgress.objects.filter(user=request.user).values_list("key", flat=True))
    return Response({"completed": keys})
