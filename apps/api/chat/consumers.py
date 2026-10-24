"""ChatConsumer : WebSocket par chaîne, anti-spam Redis, modération streamer."""

from __future__ import annotations

import logging
import time
import unicodedata
import uuid

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from channels_app.models import Channel

from .models import ChatBan, ChatIpBan, ChatUserIp, ModAction
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

logger = logging.getLogger(__name__)

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
def _has_active_ip_ban(channel_id: int, ip: str | None) -> bool:
    if not ip:
        return False
    qs = ChatIpBan.objects.filter(channel_id=channel_id, ip=ip)
    return any(b.is_active() for b in qs)


@database_sync_to_async
def _record_user_ip(channel, user, ip: str | None) -> None:
    if not ip:
        return
    ChatUserIp.objects.update_or_create(channel=channel, user=user, defaults={"ip": ip})


@database_sync_to_async
def _user_last_ip(channel_id: int, user_id: int) -> str | None:
    row = ChatUserIp.objects.filter(channel_id=channel_id, user_id=user_id).first()
    return row.ip if row else None


@database_sync_to_async
def _upsert_ip_ban(channel, ip, until, created_by, reason=""):
    ChatIpBan.objects.update_or_create(
        channel=channel,
        ip=ip,
        defaults={"until": until, "created_by": created_by, "reason": reason},
    )


@database_sync_to_async
def _delete_ip_ban(channel_id: int, ip: str) -> int:
    deleted, _ = ChatIpBan.objects.filter(channel_id=channel_id, ip=ip).delete()
    return deleted


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


def _detect_chat_spam(entries: list[tuple[int, str]]) -> tuple[bool, str]:
    from safety.anticheat import detect_chat_spam

    return detect_chat_spam(entries)


@database_sync_to_async
def _flag_chat_bot(user_id: int, channel_id: int, reason: str) -> None:
    from accounts.models import User
    from channels_app.models import Channel
    from safety.anticheat import flag_chat_bot

    user = User.objects.filter(pk=user_id).first()
    channel = Channel.objects.filter(pk=channel_id).first()
    if user and channel:
        flag_chat_bot(user, channel, reason)


# Rechargement des réglages du chat au plus toutes les N secondes par connexion.
SETTINGS_TTL_S = 10


@database_sync_to_async
def _load_chat_settings(channel_id: int) -> dict:
    """Réglages du chat + mots interdits de la chaîne (rechargés périodiquement)."""
    from .models import ChannelBannedWord

    row = (
        Channel.objects.filter(pk=channel_id)
        .values(
            "chat_followers_only",
            "chat_follow_min_minutes",
            "chat_subscribers_only",
            "chat_emotes_only",
            "chat_slow_seconds",
            "chat_min_account_age_days",
            "automod",
        )
        .first()
        or {}
    )
    row["banned_words"] = set(
        ChannelBannedWord.objects.filter(channel_id=channel_id).values_list("word", flat=True)
    )
    return row


@database_sync_to_async
def _access_error(user, channel, conf: dict, is_subscriber: bool) -> str | None:
    """Raison du refus d'écrire (followers / abonnés seulement, âge du compte), ou None."""
    now = timezone.now()
    if conf.get("chat_subscribers_only") and not is_subscriber:
        return "Chat réservé aux abonnés."
    if conf.get("chat_followers_only"):
        from social.models import Follow

        follow = Follow.objects.filter(follower=user, followee_id=channel.user_id).first()
        if follow is None:
            return "Chat réservé aux followers : suis la chaîne pour écrire."
        minutes = conf.get("chat_follow_min_minutes") or 0
        if minutes and follow.created_at > now - timezone.timedelta(minutes=minutes):
            return f"Chat réservé aux followers depuis au moins {minutes} min."
    days = conf.get("chat_min_account_age_days") or 0
    if days and user.date_joined > now - timezone.timedelta(days=days):
        return f"Ton compte doit avoir au moins {days} jour(s) pour écrire ici."
    return None


def _only_emotes(text: str) -> bool:
    """Vrai si le message ne contient que des emojis (et des espaces)."""
    return all(
        ch.isspace() or ch in "\u200d\ufe0f" or unicodedata.category(ch) in ("So", "Sk")
        for ch in text
    )


@database_sync_to_async
def _log_mod(channel_id, actor_id, action, target_id=None, duration_s=0, detail="") -> None:
    """Journal de modération (widget « Mod Actions ») + journal d'audit global."""
    ModAction.objects.create(
        channel_id=channel_id,
        actor_id=actor_id,
        target_user_id=target_id,
        action=action,
        duration_s=int(duration_s or 0),
        detail=(detail or "")[:200],
    )
    if action != ModAction.Action.AUTOMOD:
        try:
            from accounts.models import User
            from audit.services import record

            record(
                User(pk=actor_id) if actor_id else None,
                f"chat.{action}",
                target=Channel(pk=channel_id),
                meta={"target_user": target_id, "detail": detail},
            )
        except Exception:  # noqa: BLE001 - l'audit ne bloque jamais la modération
            logger.warning("audit chat.%s non enregistré", action)


@database_sync_to_async
def _save_slow_seconds(channel_id: int, seconds: int) -> None:
    Channel.objects.filter(pk=channel_id).update(chat_slow_seconds=max(0, int(seconds)))


@database_sync_to_async
def _chat_badges(user_id: int, channel_id: int) -> dict:
    """Niveau (Aura dépensée à vie) + badge de don pour cette chaîne, à jour."""
    from accounts.models import User
    from gamification.support import chat_badges

    spent = User.objects.filter(pk=user_id).values_list("lifetime_aura_spent", flat=True).first()
    return chat_badges(user_id, channel_id, spent or 0)


@database_sync_to_async
def _load_subscriber_ids(channel) -> set[int]:
    from subscriptions.services import subscriber_user_ids

    return subscriber_user_ids(channel)


def _client_ip(scope) -> str | None:
    """IP réelle du client derrière les proxys (même règle que config.client_ip)."""
    from config.client_ip import client_ip_from_scope

    return client_ip_from_scope(scope)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    channel_obj: Channel | None = None
    group_name: str = ""
    banned_words: set[str] = frozenset()
    subscriber_ids: set[int] = frozenset()
    is_shadow_banned: bool = False
    client_ip: str | None = None
    _msg_log: list | None = None
    _bot_flagged: bool = False
    _conf: dict | None = None
    _conf_at: float = 0.0

    async def connect(self) -> None:
        self._msg_log = []
        self._bot_flagged = False
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

        self.client_ip = _client_ip(self.scope)

        # Ban IP → connexion refusée (s'applique aussi aux anonymes), sauf streamer.
        if not is_streamer and await _has_active_ip_ban(self.channel_obj.id, self.client_ip):
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

        # Mémorise la dernière IP de l'utilisateur (cible des bans IP).
        if getattr(user, "is_authenticated", False):
            await _record_user_ip(self.channel_obj, user, self.client_ip)

        self.group_name = f"chat.{self.channel_obj.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        self.banned_words = await _load_banned_words()
        self.subscriber_ids = await _load_subscriber_ids(self.channel_obj)
        # Le streamer (dashboard, page de sa chaîne) ne compte pas comme spectateur.
        self._counted = not is_streamer
        if self._counted:
            count = await incr_viewers(self.channel_obj.id)
            await _record_peak(self.channel_obj.id, count)

    async def disconnect(self, code: int) -> None:  # noqa: ARG002
        if self.group_name and self.channel_obj is not None:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            if getattr(self, "_counted", False):
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

        conf = await self._chat_settings()
        # Le streamer et l'équipe Neyla ne sont pas soumis aux restrictions du chat.
        exempt = is_streamer or getattr(user, "role", "") in ("admin", "moderator")
        if not exempt:
            denied = await _access_error(
                user, self.channel_obj, conf, user.pk in self.subscriber_ids
            )
            if denied:
                await self.send_json({"type": "error", "detail": denied})
                return
            if conf.get("chat_emotes_only") and not _only_emotes(text):
                await self.send_json(
                    {"type": "error", "detail": "Mode emotes : uniquement des emojis."}
                )
                return

        # Mots interdits : liste globale (connexion) + liste de la chaîne (réglages).
        lowered = text.lower()
        words = self.banned_words | conf.get("banned_words", set())
        if not is_streamer and words and any(w in lowered for w in words):
            await self.send_json({"type": "error", "detail": "Message bloqué (terme interdit)."})
            return

        if not exempt:
            from safety.automod import check as automod_check

            blocked = automod_check(text, conf.get("automod"))
            if blocked:
                await self.send_json(
                    {"type": "error", "detail": "Message bloqué par la modération automatique."}
                )
                await _log_mod(
                    self.channel_obj.id,
                    None,
                    ModAction.Action.AUTOMOD,
                    target_id=user.pk,
                    detail=f"{blocked} : {text[:120]}",
                )
                return

        # Rate limit personnel (avec slow-mode si activé).
        slow = max(await get_slowmode(self.channel_obj.id), conf.get("chat_slow_seconds") or 0)
        interval = max(slow, MIN_INTERVAL_S)
        if not await check_rate_limit(self.channel_obj.id, user.pk, interval):
            await self.send_json({"type": "error", "detail": "Tu vas trop vite."})
            return

        badges = await _chat_badges(user.pk, self.channel_obj.id)
        msg = {
            "id": str(uuid.uuid4()),
            "user": {
                "username": user.username,
                "display_name": user.display_name or user.username,
                "role": user.role,
                "is_subscriber": user.pk in self.subscriber_ids,
                **badges,
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

        # Détection de bot de chat (best-effort, une seule alerte par connexion).
        self._msg_log.append((msg["ts"], text))
        self._msg_log = self._msg_log[-20:]
        if not self._bot_flagged:
            suspect, reason = _detect_chat_spam(self._msg_log)
            if suspect:
                self._bot_flagged = True
                await _flag_chat_bot(user.pk, self.channel_obj.id, reason)

    async def _chat_settings(self) -> dict:
        now = time.monotonic()
        if self._conf is None or now - self._conf_at > SETTINGS_TTL_S:
            self._conf = await _load_chat_settings(self.channel_obj.id)
            self._conf_at = now
        return self._conf

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

    async def chat_ipban(self, event):
        """Ferme toute connexion (y compris anonyme) issue de l'IP bannie."""
        u = self.scope.get("user")
        is_streamer = (
            self.channel_obj is not None
            and getattr(u, "is_authenticated", False)
            and u.pk == self.channel_obj.user_id
        )
        if not is_streamer and self.client_ip and self.client_ip == event["ip"]:
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
            await _save_slow_seconds(self.channel_obj.id, seconds)
            self._conf = None
            await _log_mod(
                self.channel_obj.id, streamer.pk, ModAction.Action.SLOWMODE, duration_s=seconds
            )
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
            await _log_mod(
                self.channel_obj.id,
                streamer.pk,
                ModAction.Action.TIMEOUT if cmd == "/timeout" else ModAction.Action.BAN,
                target_id=target.pk,
                duration_s=minutes * 60 if cmd == "/timeout" else 0,
                detail=reason,
            )
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
            await _log_mod(
                self.channel_obj.id,
                streamer.pk,
                ModAction.Action.SHADOW if cmd == "/shadow" else ModAction.Action.UNSHADOW,
                target_id=target.pk,
            )
            verb = "shadow-banni" if cmd == "/shadow" else "réintégré"
            return await self.send_json({"type": "system", "detail": f"@{target.username} {verb}."})

        if cmd == "/ipban" and len(parts) >= 2:
            target = await _resolve_target_user(parts[1])
            if target is None:
                return await self.send_json({"type": "error", "detail": "Utilisateur introuvable."})
            if target.pk == streamer.pk:
                return await self.send_json(
                    {"type": "error", "detail": "Action impossible sur toi-même."}
                )
            ip = await _user_last_ip(self.channel_obj.id, target.pk)
            if not ip:
                return await self.send_json(
                    {"type": "error", "detail": "IP inconnue pour cet utilisateur."}
                )
            try:
                minutes = max(1, int(parts[2])) if len(parts) >= 3 else 0
            except ValueError:
                minutes = 0
            until = timezone.now() + timezone.timedelta(minutes=minutes) if minutes else None
            reason = f"ipban {ip}"
            # Ban du compte ET de l'IP, puis fermeture des connexions concernées.
            await _upsert_ban(self.channel_obj, target, until, streamer, reason=reason)
            await _upsert_ip_ban(self.channel_obj, ip, until, streamer, reason=reason)
            await _log_mod(
                self.channel_obj.id,
                streamer.pk,
                ModAction.Action.IPBAN,
                target_id=target.pk,
                duration_s=minutes * 60,
                detail=reason,
            )
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "chat.kick", "user_id": target.pk, "reason": reason},
            )
            await self.channel_layer.group_send(
                self.group_name, {"type": "chat.ipban", "ip": ip, "reason": reason}
            )
            return await self.send_json(
                {"type": "system", "detail": f"@{target.username} banni (IP {ip})."}
            )

        if cmd == "/ipunban" and len(parts) >= 2:
            removed = await _delete_ip_ban(self.channel_obj.id, parts[1])
            await _log_mod(
                self.channel_obj.id, streamer.pk, ModAction.Action.IPUNBAN, detail=parts[1]
            )
            return await self.send_json(
                {"type": "system", "detail": f"IP {parts[1]} : {removed} ban(s) levé(s)."}
            )

        if cmd == "/delete" and len(parts) >= 2:
            await delete_message(self.channel_obj.id, parts[1])
            await _log_mod(self.channel_obj.id, streamer.pk, ModAction.Action.DELETE)
            await self.channel_layer.group_send(
                self.group_name, {"type": "chat.delete", "id": parts[1]}
            )
            return

        if cmd == "/unban" and len(parts) >= 2:
            target = await _resolve_target_user(parts[1])
            if target is None:
                return
            await _delete_ban(self.channel_obj.id, target.pk)
            await _log_mod(
                self.channel_obj.id, streamer.pk, ModAction.Action.UNBAN, target_id=target.pk
            )
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "chat.shadow", "user_id": target.pk, "on": False},
            )
            return await self.send_json(
                {"type": "system", "detail": f"@{target.username} débanni."}
            )

        await self.send_json({"type": "error", "detail": "Commande inconnue."})


@database_sync_to_async
def _channel_id_by_overlay_token(token: str) -> int | None:
    if not token:
        return None
    row = Channel.objects.filter(overlay_token=token).only("id").first()
    return row.id if row else None


class OverlayConsumer(AsyncJsonWebsocketConsumer):
    """Flux temps réel d'alertes pour l'overlay OBS (auth par jeton dans l'URL)."""

    group_name: str = ""

    async def connect(self) -> None:
        token = self.scope["url_route"]["kwargs"]["token"]
        channel_id = await _channel_id_by_overlay_token(token)
        if not channel_id:
            await self.close(code=CLOSE_FORBIDDEN)
            return
        self.group_name = f"overlay.{channel_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code: int) -> None:  # noqa: ARG002
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def overlay_alert(self, event):
        await self.send_json({"type": "alert", "alert": event["alert"]})
