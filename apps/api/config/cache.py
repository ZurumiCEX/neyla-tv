"""Cache Redis tolérant aux pannes.

django-ratelimit n'intercepte pas les erreurs de connexion Redis : sans ce
garde-fou, une panne Redis transformerait chaque connexion / inscription en
erreur 500. Ici, une erreur Redis se comporte comme un cache vide ; combiné à
RATELIMIT_FAIL_OPEN, les limites sont simplement suspendues le temps de la panne.
"""

from __future__ import annotations

import logging

from django.core.cache.backends.redis import RedisCache
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class ResilientRedisCache(RedisCache):
    def _warn(self, op: str) -> None:
        logger.warning("cache redis indisponible (%s) : opération ignorée", op)

    def add(self, *args, **kwargs):
        try:
            return super().add(*args, **kwargs)
        except RedisError:
            self._warn("add")
            return False

    def get(self, key, default=None, version=None):
        try:
            return super().get(key, default, version)
        except RedisError:
            self._warn("get")
            return default

    def set(self, *args, **kwargs):
        try:
            return super().set(*args, **kwargs)
        except RedisError:
            self._warn("set")
            return None

    def incr(self, key, delta=1, version=None):
        try:
            return super().incr(key, delta, version)
        except RedisError as exc:
            self._warn("incr")
            raise ValueError("cache indisponible") from exc

    def delete(self, key, version=None):
        try:
            return super().delete(key, version)
        except RedisError:
            self._warn("delete")
            return False
