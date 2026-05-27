"""Helpers Redis pour le chat : messages cappés, viewers, slow-mode, rate-limit."""

from __future__ import annotations

import json
from typing import Any

import redis
import redis.asyncio as aredis
from django.conf import settings

MAX_MESSAGES = 100


def _key(kind: str, channel_id: int) -> str:
    return f"chat:{kind}:{channel_id}"


# --- Async (utilisé par le consumer Channels) ---


def _aclient() -> aredis.Redis:
    return aredis.from_url(settings.REDIS_URL, decode_responses=True)


async def append_message(channel_id: int, msg: dict[str, Any]) -> None:
    r = _aclient()
    try:
        pipe = r.pipeline()
        pipe.rpush(_key("msgs", channel_id), json.dumps(msg))
        pipe.ltrim(_key("msgs", channel_id), -MAX_MESSAGES, -1)
        await pipe.execute()
    finally:
        await r.aclose()


async def delete_message(channel_id: int, msg_id: str) -> bool:
    """Retire un message (par id) de la liste cappée. True si trouvé."""
    r = _aclient()
    try:
        key = _key("msgs", channel_id)
        raw = await r.lrange(key, 0, -1)
        kept = [m for m in raw if json.loads(m).get("id") != msg_id]
        if len(kept) == len(raw):
            return False
        pipe = r.pipeline()
        pipe.delete(key)
        if kept:
            pipe.rpush(key, *kept)
        await pipe.execute()
        return True
    finally:
        await r.aclose()


async def get_slowmode(channel_id: int) -> int:
    r = _aclient()
    try:
        val = await r.get(_key("slowmode", channel_id))
        return int(val) if val else 0
    finally:
        await r.aclose()


async def set_slowmode(channel_id: int, seconds: int) -> None:
    r = _aclient()
    try:
        key = _key("slowmode", channel_id)
        if seconds <= 0:
            await r.delete(key)
        else:
            await r.set(key, seconds)
    finally:
        await r.aclose()


async def check_rate_limit(channel_id: int, user_id: int, interval_s: float) -> bool:
    """Retourne True si l'envoi est autorisé (pose la sentinelle), False sinon."""
    r = _aclient()
    try:
        key = f"chatrl:{channel_id}:{user_id}"
        px = max(int(interval_s * 1000), 100)
        ok = await r.set(key, "1", nx=True, px=px)
        return bool(ok)
    finally:
        await r.aclose()


async def incr_viewers(channel_id: int) -> int:
    r = _aclient()
    try:
        new = await r.incr(_key("viewers", channel_id))
        await r.expire(_key("viewers", channel_id), 60 * 60)
        return int(new)
    finally:
        await r.aclose()


async def decr_viewers(channel_id: int) -> int:
    r = _aclient()
    try:
        new = await r.decr(_key("viewers", channel_id))
        if new < 0:
            await r.set(_key("viewers", channel_id), 0)
            return 0
        return int(new)
    finally:
        await r.aclose()


# --- Sync (utilisé par les vues HTTP) ---


def get_viewers_count(channel_id: int) -> int:
    client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        val = client.get(_key("viewers", channel_id))
        return max(int(val), 0) if val else 0
    except (redis.RedisError, ValueError):
        return 0


def bulk_viewers_count(channel_ids: list[int]) -> dict[int, int]:
    if not channel_ids:
        return {}
    client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        keys = [_key("viewers", cid) for cid in channel_ids]
        values = client.mget(keys)
        result: dict[int, int] = {}
        for cid, raw in zip(channel_ids, values, strict=True):
            try:
                result[cid] = max(int(raw), 0) if raw else 0
            except (TypeError, ValueError):
                result[cid] = 0
        return result
    except redis.RedisError:
        return dict.fromkeys(channel_ids, 0)


def get_history(channel_id: int, limit: int = MAX_MESSAGES) -> list[dict[str, Any]]:
    client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        raw = client.lrange(_key("msgs", channel_id), -limit, -1)
        return [json.loads(m) for m in raw]
    except redis.RedisError:
        return []
