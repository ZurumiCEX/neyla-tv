"""Vérifie la configuration Cloudflare Stream end-to-end.

Crée un live input temporaire, contrôle la réponse, puis le supprime.
Utile pour valider rapidement les identifiants en production ou staging.

    python manage.py verify_cloudflare_stream
"""

from __future__ import annotations

import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from channels_app.cloudflare import (
    CloudflareStreamError,
    FakeCloudflareStreamClient,
    get_client,
)


class Command(BaseCommand):
    help = "Vérifie la connexion à Cloudflare Stream (création + suppression d'un live input)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--label",
            default=f"neyla-verify-{int(time.time())}",
            help="Étiquette du live input de test.",
        )
        parser.add_argument(
            "--keep",
            action="store_true",
            help="Ne pas supprimer le live input après test (à utiliser avec précaution).",
        )

    def handle(self, *args, **options):
        label: str = options["label"]
        keep: bool = options["keep"]

        token = settings.CLOUDFLARE_API_TOKEN
        token_label = f"(défini, {len(token)} car.)" if token else "(vide → mode FAKE)"
        secret_label = "(défini)" if settings.CLOUDFLARE_WEBHOOK_SECRET else "(vide)"
        self.stdout.write(self.style.MIGRATE_HEADING("Configuration"))
        self.stdout.write(
            f"  CLOUDFLARE_ACCOUNT_ID    : {settings.CLOUDFLARE_ACCOUNT_ID or '(vide)'}"
        )
        self.stdout.write(f"  CLOUDFLARE_API_TOKEN     : {token_label}")
        self.stdout.write(f"  CLOUDFLARE_WEBHOOK_SECRET: {secret_label}")

        client = get_client()
        if isinstance(client, FakeCloudflareStreamClient):
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠ Mode FAKE actif : CLOUDFLARE_API_TOKEN est vide. "
                    "Définis-le pour appeler la vraie API Cloudflare."
                )
            )

        self.stdout.write(self.style.MIGRATE_HEADING(f"\nCréation du live input « {label} »"))
        try:
            live = client.create_live_input(label)
        except CloudflareStreamError as exc:
            raise CommandError(f"Échec de la création : {exc}") from exc

        self.stdout.write(self.style.SUCCESS("  ✓ live input créé"))
        self.stdout.write(f"    uid              : {live.uid}")
        self.stdout.write(f"    rtmps_url        : {live.rtmps_url}")
        key = live.rtmps_key
        masked_key = f"{key[:8]}…{key[-4:]}" if len(key) > 12 else key
        self.stdout.write(f"    rtmps_key        : {masked_key}")
        self.stdout.write(f"    hls_playback_url : {live.hls_playback_url}")

        if keep:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠ --keep activé : le live input {live.uid} N'EST PAS supprimé."
                )
            )
            return

        self.stdout.write(self.style.MIGRATE_HEADING("\nSuppression du live input"))
        try:
            client.delete_live_input(live.uid)
        except CloudflareStreamError as exc:
            raise CommandError(f"Échec de la suppression : {exc}") from exc
        self.stdout.write(self.style.SUCCESS("  ✓ live input supprimé"))

        self.stdout.write(self.style.SUCCESS("\n✓ Cloudflare Stream opérationnel."))
