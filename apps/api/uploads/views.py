"""Endpoints d'upload d'images (avatar, bannière, vignette de jeu)."""

from __future__ import annotations

import contextlib

from django.core.files.storage import default_storage
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.permissions import IsAdminRole
from catalog.models import Game
from channels_app.models import Channel

from . import services


def _upload(request: Request, folder: str, replaces: str = "") -> str:
    file = request.FILES.get("file")
    if file is None:
        raise ValidationError({"file": "Fichier manquant."})
    try:
        return services.upload_image(file, folder, request=request, replaces=replaces)
    except services.UploadError as exc:
        raise ValidationError({"file": str(exc)}) from exc


def _scan_image(url: str, source: str, *, user=None, channel=None) -> None:
    """Analyse anti-violation best-effort (n'interrompt jamais l'upload)."""
    with contextlib.suppress(Exception):
        from safety.services import scan_image

        scan_image(url, source, user=user, channel=channel)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_avatar(request: Request) -> Response:
    url = _upload(request, "avatars", replaces=request.user.avatar_url)
    request.user.avatar_url = url
    request.user.save(update_fields=["avatar_url"])
    _scan_image(url, "avatar", user=request.user)
    return Response({"url": url}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_banner(request: Request) -> Response:
    channel, _ = Channel.objects.get_or_create(
        user=request.user, defaults={"slug": request.user.username}
    )
    url = _upload(request, "banners", replaces=channel.banner_url)
    channel.banner_url = url
    channel.save(update_fields=["banner_url", "updated_at"])
    _scan_image(url, "banner", user=request.user, channel=channel)
    return Response({"url": url}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAdminRole])
@parser_classes([MultiPartParser, FormParser])
def upload_game_box_art(request: Request, slug: str) -> Response:
    game = Game.objects.filter(slug=slug.lower()).first()
    if game is None:
        raise NotFound("Jeu introuvable.")
    url = _upload(request, "games", replaces=game.box_art_url)
    game.box_art_url = url
    game.save(update_fields=["box_art_url"])
    return Response({"url": url}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([AllowAny])
def media(request: Request, path: str):
    """Sert les images stockées localement (mode sans R2 : dev, démo)."""
    if ".." in path or not path.startswith("uploads/") or not default_storage.exists(path):
        raise Http404
    response = FileResponse(default_storage.open(path, "rb"))
    response["Cache-Control"] = "public, max-age=31536000, immutable"
    response["X-Content-Type-Options"] = "nosniff"
    return response
