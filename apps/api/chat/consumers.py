"""ChatConsumer : WebSocket par chaîne, anti-spam Redis, modération streamer."""

from __future__ import annotations

import time
import uuid

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from channels_app.models import Channel

from .models import ChatBan
from .redis_store import (
    append_message,
    check_rate_limit,
    decr_viewers,
    delete_message,
    get_slowmode,
    incr_viewers,
    set_slowmode,
)

CLOSE_AUTH_REQUIRED = 4001
CLOSE_FORBIDDEN = 4403
CLOSE_NOT_FOUND = 4404

MIN_INTERVAL_S = 1.5
MAX_CONTENT_LEN = 500


@database_sync_to_async
def _get_channel(slug: str) -> Channel | None:
    return Channel.objects.select_related("user").filter(slug=slug.lower()).first()


@database_sync_to_async
def _has_active_hard_ban(channel_id: int, user_id: int) -> bool:
    """Ban "dur" (ferme la connexion). Les shadow bans n'entrent pas en compte."""
    qs = ChatBan.objects.filter(channel_id=channel_id, user_id=user_id, shadow=False)
    return any(ban.is_active() for ban in qs)


@database_sync_to_async
def _has_active_shadow_ban(channel_id: int, user_id: int) -> bool:
    qs = ChatBan.objects.filter(channel_id=channel_id, user_id=user_id, shadow=True)
    return any(ban.is_active() for ban in qs)


@database_sync_to_async
def _resolve_target_user(username: str):
    from accounts.models import User

    return User.objects.filter(username=username.lower()).first()


@database_sync_to_async
def _upsert_ban(channel, user, until, created_by, reason="", shadow=False):
    ban, _ = ChatBan.objects.update_or_create(
        channel=channel,
        user=user,
        defaults={
            "until": until,
            "created_by": created_by,
            "reason": reason,
            "shadow": shadow,
        },
    )
    return ban


@database_sync_to_async
def _delete_ban(channel_id: int, user_id: int) -> int:
    deleted, _ = ChatBan.objects.filter(channel_id=channel_id, user_id=user_id).delete()
    return deleted


@database_sync_to_async
def _record_peak(channel_id: int, viewers: int) -> None:
    from channels_app.services import record_session_peak

    record_session_peak(channel_id, viewers)


@database_sync_to_async
def _load_banned_words() -> set[str]:
    from moderation.services import get_banned_words

    return get_banned_words()


@database_sync_to_async
def _load_subscriber_ids(channel) -> set[int]:
    from subscriptions.services import subscriber_user_ids

    return subscriber_user_ids(channel)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    channel_obj: Channel | None = None
    group_name: str = ""
    banned_words: set[str] = frozenset()
    subscriber_ids: set[int] = frozenset()
    is_shadow_banned: bool = False

    async def connect(self) -> None:
        slug = self.scope["url_route"]["kwargs"]["slug"]
        self.channel_obj = await _get_channel(slug)
        if self.channel_obj is None:
            await self.close(code=CLOSE_NOT_FOUND)
            return

        user = self.scope.get("user")
        is_streamer = (
            user is not None
            and getattr(user, "is_authenticated", False)
            and user.pk == self.channel_obj.user_id
        )

        # Connexion permise si la chaîne est en live, ou si on est le streamer.
        if not self.channel_obj.is_live and not is_streamer:
            await self.close(code=CLOSE_FORBIDDEN)
            return

        # Ban "dur" → connexion refusée (uniquement pour les authentifiés).
        if getattr(user, "is_authenticated", False) and await _has_active_hard_ban(
            self.channel_obj.id, user.pk
        ):
            await self.close(code=CLOSE_FORBIDDEN)
            return

        # Shadow ban → connexion permise, messages non diffusés aux autres.
        self.is_shadow_banned = bool(
            getattr(user, "is_authenticated", False)
            and await _has_active_shadow_ban(self.channel_obj.id, user.pk)
        )

        self.group_name = f"chat.{self.channel_obj.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        self.banned_words = await _load_banned_words()
        self.subscriber_ids = await _load_subscriber_ids(self.channel_obj)
        count = await incr_viewers(self.channel_obj.id)
        await _record_peak(self.channel_obj.id, count)

    async def disconnect(self, code: int) -> None:  # noqa: ARG002
        if self.group_name and self.channel_obj is not None:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            await decr_viewers(self.channel_obj.id)

    async def receive_json(self, content, **kwargs):  # noqa: ARG002
        user = self.scope.get("user")
        if not getattr(user, "is_authenticated", False):
            await self.send_json({"type": "error", "detail": "Connexion requise."})
            return
        text = (content.get("content") or "").strip()
        if not text or self.channel_obj is None:
            return
        if len(text) > MAX_CONTENT_LEN:
            text = text[:MAX_CONTENT_LEN]

        is_streamer = user.pk == self.channel_obj.user_id

        if text.startswith("/"):
            if is_streamer:
                await self._handle_command(user, text)
            else:
                await self.send_json(
                    {"type": "error", "detail": "Commandes réservées au streamer."}
                )
            return

        # Filtre mots interdits (chargé à la connexion).
        if self.banned_words and any(w in text.lower() for w in self.banned_words):
            await self.send_json({"type": "error", "detail": "Message bloqué (terme interdit)."})
            return

        # Rate limit personnel (avec slow-mode si activé).
        slow = await get_slowmode(self.channel_obj.id)
        interval = max(slow, MIN_INTERVAL_S)
        if not await check_rate_limit(self.channel_obj.id, user.pk, interval):
            await self.send_json({"type": "error", "detail": "Tu vas trop vite."})
            return

        msg = {
            "id": str(uuid.uuid4()),
            "user": {
                "username": user.username,
                "display_name": user.display_name or user.username,
                "role": user.role,
                "is_subscriber": user.pk in self.subscriber_ids,
            },
            "content": text,
            "ts": int(time.time() * 1000),
        }
        # Shadow ban : l'auteur voit son message, mais il n'est ni historisé
        # ni diffusé aux autres spectateurs.
        if self.is_shadow_banned:
            await self.send_json({"type": "message", "msg": msg})
            return

        await append_message(self.channel_obj.id, msg)
        await self.channel_layer.group_send(self.group_name, {"type": "chat.message", "msg": msg})

    # Handler du group_send.
    async def chat_message(self, event):
        await self.send_json({"type": "message", "msg": event["msg"]})

    async def chat_shadow(self, event):
        """Active/désactive le shadow ban de cette connexion si elle est ciblée."""
        u = self.scope.get("user")
        if u and getattr(u, "pk", None) == event["user_id"]:
            self.is_shadow_banned = bool(event["on"])

    async def chat_kick(self, event):
        if self.scope.get("user") and self.scope["user"].pk == event["user_id"]:
            await self.send_json({"type": "kicked", "detail": event.get("reason", "")})
            await self.close(code=CLOSE_FORBIDDEN)

    async def chat_delete(self, event):
        await self.send_json({"type": "delete", "id": event["id"]})

    async def _handle_command(self, streamer, text: str) -> None:
        parts = text.split(maxsplit=2)
        cmd = parts[0].lower()
        if cmd == "/slowmode" and len(parts) >= 2:
            try:
                seconds = max(0, int(parts[1]))
            except ValueError:
                return await self.send_json({"type": "error", "detail": "/slowmode <secondes>"})
            await set_slowmode(self.channel_obj.id, seconds)
            return await self.send_json({"type": "system", "detail": f"Slow-mode → {seconds}s"})

        if cmd in ("/timeout", "/ban") and len(parts) >= 2:
            target = await _resolve_target_user(parts[1])
            if target is None:
                return await self.send_json({"type": "error", "detail": "Utilisateur introuvable."})
            if target.pk == streamer.pk:
                return await self.send_json(
                    {"type": "error", "detail": "Tu ne peux pas te bannir toi-même."}
                )
            if cmd == "/timeout":
                try:
                    minutes = max(1, int(parts[2])) if len(parts) >= 3 else 10
                except ValueError:
                    minutes = 10
                until = timezone.now() + timezone.timedelta(minutes=minutes)
                reason = f"timeout {minutes}min"
            else:
                until = None
                reason = "ban permanent"
            await _upsert_ban(self.channel_obj, target, until, streamer, reason=reason)
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "chat.kick", "user_id": target.pk, "reason": reason},
            )
            return await self.send_json(
                {"type": "system", "detail": f"{cmd} @{target.username} ({reason})"}
            )

        if cmd in ("/shadow", "/unshadow") and len(parts) >= 2:
            target = await _resolve_target_user(parts[1])
            if target is None:
                return await self.send_json({"type": "error", "detail": "Utilisateur introuvable."})
            if target.pk == streamer.pk:
                return await self.send_json(
                    {"type": "error", "detail": "Action impossible sur toi-même."}
                )
            if cmd == "/shadow":
                await _upsert_ban(
                    self.channel_obj, target, None, streamer, reason="shadow", shadow=True
                )
            else:
                await _delete_ban(self.channel_obj.id, target.pk)
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "chat.shadow", "user_id": target.pk, "on": cmd == "/shadow"},
            )
            verb = "shadow-banni" if cmd == "/shadow" else "réintégré"
            return await self.send_json({"type": "system", "detail": f"@{target.username} {verb}."})

        if cmd == "/delete" and len(parts) >= 2:
            await delete_message(self.channel_obj.id, parts[1])
            await self.channel_layer.group_send(
                self.group_name, {"type": "chat.delete", "id": parts[1]}
            )
            return

        if cmd == "/unban" and len(parts) >= 2:
            target = await _resolve_target_user(parts[1])
            if target is None:
                return
            await _delete_ban(self.channel_obj.id, target.pk)
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "chat.shadow", "user_id": target.pk, "on": False},
            )
            return await self.send_json(
                {"type": "system", "detail": f"@{target.username} débanni."}
            )

        await self.send_json({"type": "error", "detail": "Commande inconnue."})
