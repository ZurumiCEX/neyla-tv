"""Vérifie la configuration Bunny Stream de bout en bout.

Crée un live stream temporaire, contrôle la réponse (en affichant la réponse
brute pour diagnostiquer un écart de schéma), lit son état, puis le supprime.

    python manage.py verify_bunny_stream
"""

from __future__ import annotations

import json
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from channels_app.bunny import BunnyStreamError, get_client


class Command(BaseCommand):
    help = "Vérifie la connexion à Bunny Stream (création + état + suppression d'un live)."

    def add_arguments(self, parser):
        parser.add_argument("--label", default=f"neyla-verify-{int(time.time())}")
        parser.add_argument(
            "--keep",
            action="store_true",
            help="Ne pas supprimer le live stream de test (à utiliser avec précaution).",
        )

    def handle(self, *args, **options):
        label: str = options["label"]
        key = settings.BUNNY_STREAM_API_KEY
        key_label = f"(défini, {len(key)} car.)" if key else "(vide → mode FAKE)"
        library = settings.BUNNY_STREAM_LIBRARY_ID or "(vide)"
        cdn = settings.BUNNY_STREAM_CDN_HOSTNAME or "(vide)"
        self.stdout.write(self.style.MIGRATE_HEADING("Configuration"))
        self.stdout.write(f"  BUNNY_STREAM_LIBRARY_ID  : {library}")
        self.stdout.write(f"  BUNNY_STREAM_API_KEY     : {key_label}")
        self.stdout.write(f"  BUNNY_STREAM_CDN_HOSTNAME: {cdn}")

        client = get_client()
        if client.is_fake:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠ Mode FAKE actif : BUNNY_STREAM_API_KEY est vide (aucun appel réseau)."
                )
            )

        self.stdout.write(self.style.MIGRATE_HEADING(f"\nCréation du live « {label} »"))
        try:
            live = client.create_live_stream(label)
        except BunnyStreamError as exc:
            raise CommandError(f"Échec de la création : {exc}") from exc
        sk = live.stream_key
        masked = f"{sk[:6]}…{sk[-4:]}" if len(sk) > 12 else (sk or "(vide)")
        self.stdout.write(self.style.SUCCESS("  ✓ live stream créé"))
        self.stdout.write(f"    stream_id    : {live.stream_id}")
        self.stdout.write(f"    ingest_url   : {live.ingest_url}")
        self.stdout.write(f"    stream_key   : {masked}")
        self.stdout.write(f"    playback_url : {live.playback_url or '(vide)'}")
        if live.raw:
            safe = {k: ("***" if "key" in k.lower() else v) for k, v in live.raw.items()}
            self.stdout.write("    réponse brute: " + json.dumps(safe, default=str)[:800])
        if not live.stream_key or not live.playback_url:
            self.stdout.write(
                self.style.WARNING(
                    "  ⚠ clé ou URL de lecture absente : ajuster le parsing de "
                    "channels_app/bunny.py d'après la réponse brute ci-dessus."
                )
            )

        try:
            status = client.get_live_status(live.stream_id)
            state = "EN DIRECT" if status.is_live else "hors ligne"
            self.stdout.write(f"  état actuel  : {state}")
        except BunnyStreamError as exc:
            self.stdout.write(self.style.WARNING(f"  ⚠ lecture d'état impossible : {exc}"))

        if options["keep"]:
            self.stdout.write(self.style.WARNING(f"\n⚠ --keep : {live.stream_id} conservé."))
            return
        try:
            client.delete_live_stream(live.stream_id)
        except BunnyStreamError as exc:
            raise CommandError(f"Échec de la suppression : {exc}") from exc
        self.stdout.write(self.style.SUCCESS("  ✓ live stream supprimé"))
        self.stdout.write(self.style.SUCCESS("\n✓ Bunny Stream opérationnel."))
