"""Annonces actives renvoyées au client selon son audience."""

from __future__ import annotations

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from .models import SiteAnnouncement


def _audience_for(request: Request) -> set[str]:
    """Audiences applicables à l'utilisateur courant (always inclut `all`)."""
    audiences = {SiteAnnouncement.Audience.ALL}
    user = getattr(request, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        audiences.add(SiteAnnouncement.Audience.ANONYMOUS)
        return audiences
    # Authentifié → streamers vs viewers selon la chaîne provisionnée.
    from channels_app.models import Channel

    is_streamer = Channel.objects.filter(user_id=user.id).exclude(live_input_uid="").exists()
    audiences.add(
        SiteAnnouncement.Audience.STREAMERS if is_streamer else SiteAnnouncement.Audience.VIEWERS
    )
    return audiences


@api_view(["GET"])
@permission_classes([AllowAny])
def active(request: Request) -> Response:
    """Annonces actives pour l'audience courante."""
    now = timezone.now()
    audiences = _audience_for(request)
    qs = SiteAnnouncement.objects.filter(
        is_active=True, starts_at__lte=now, ends_at__gte=now, audience__in=audiences
    ).order_by("-starts_at")
    results = [
        {
            "id": a.id,
            "title": a.title,
            "body": a.body,
            "level": a.level,
            "display_mode": a.display_mode,
            "dismissible": a.dismissible,
            "cta_label": a.cta_label,
            "cta_url": a.cta_url,
        }
        for a in qs
    ]
    return Response({"results": results})
