"""Vérifie la configuration de production avant les migrations (release Fly.io).

Affiche ce qui manque ou ne répond pas, sans jamais imprimer de valeur secrète.
Code de sortie 1 si une erreur bloque le déploiement.
"""

from __future__ import annotations

from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


def _host_of(url: str) -> str:
    try:
        return urlparse(url).hostname or "?"
    except ValueError:
        return "?"


class Command(BaseCommand):
    help = "Vérifie secrets, base de données et Redis avant le déploiement."

    def handle(self, *args, **options):
        errors: list[str] = []
        warnings: list[str] = []

        if settings.SECRET_KEY in ("", "dev-insecure-key"):
            errors.append("DJANGO_SECRET_KEY absent : fly secrets set DJANGO_SECRET_KEY=…")
        if not settings.DEBUG and not settings.ALLOWED_HOSTS:
            errors.append(
                "Aucun hôte autorisé : définis DJANGO_ALLOWED_HOSTS (FLY_APP_NAME est ajouté "
                "automatiquement sur Fly)."
            )

        db = settings.DATABASES["default"]
        host = db.get("HOST") or "?"
        try:
            connection.ensure_connection()
            self.stdout.write(f"[preflight] base de données OK ({host}/{db.get('NAME')})")
        except (
            Exception
        ) as exc:  # noqa: BLE001 - on veut un message lisible, quelle que soit l'erreur
            reason = str(exc).splitlines()[0][:200] if str(exc) else exc.__class__.__name__
            # psycopg ne met pas le mot de passe dans ses erreurs ; masqué par précaution.
            password = db.get("PASSWORD") or ""
            if password:
                reason = reason.replace(password, "****")
            errors.append(
                f"Connexion à la base impossible (hôte {host}) : {reason}. "
                "Vérifie DATABASE_URL (Neon : URL directe, sans « -pooler », avec "
                "?sslmode=require)."
            )

        redis_url = getattr(settings, "REDIS_URL", "")
        if not redis_url or _host_of(redis_url) == "redis":
            warnings.append(
                "REDIS_URL non configuré (chat, limites anti-abus et Celery en auront besoin) : "
                "fly secrets set REDIS_URL=rediss://…"
            )
        else:
            self.stdout.write(f"[preflight] Redis configuré ({_host_of(redis_url)})")

        for w in warnings:
            self.stdout.write(self.style.WARNING(f"[preflight] attention : {w}"))
        if errors:
            for e in errors:
                self.stderr.write(f"[preflight] ERREUR : {e}")
            raise CommandError("Configuration incomplète : déploiement interrompu.")
        self.stdout.write(self.style.SUCCESS("[preflight] configuration OK"))
