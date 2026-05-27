"""Déprovisionne les chaînes provisionnées mais jamais passées live.

Outil MANUEL pour récupérer les Live Inputs Cloudflare créés par l'ancien
comportement (auto-provision à l'inscription), désormais remplacé par le gating
streamer. Dry-run par défaut ; ajouter --apply pour exécuter réellement.

    python manage.py deprovision_unused_channels          # dry-run
    python manage.py deprovision_unused_channels --apply   # exécute
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from channels_app.cloudflare import CloudflareStreamError, get_client
from channels_app.models import Channel


class Command(BaseCommand):
    help = "Supprime les Live Inputs des chaînes provisionnées jamais passées live."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Exécute réellement les suppressions (sinon dry-run).",
        )

    def handle(self, *args, **options) -> None:
        apply = options["apply"]
        prefix = "[APPLY]" if apply else "[DRY-RUN]"
        channels = Channel.objects.exclude(live_input_uid="").filter(
            last_live_started_at__isnull=True
        )
        client = get_client()
        done = 0
        for channel in channels:
            self.stdout.write(f"{prefix} {channel.slug} (uid={channel.live_input_uid})")
            if not apply:
                done += 1
                continue
            try:
                client.delete_live_input(channel.live_input_uid)
            except CloudflareStreamError as exc:
                self.stderr.write(f"  échec suppression {channel.slug}: {exc}")
                continue
            channel.live_input_uid = ""
            channel.rtmps_url = ""
            channel.rtmps_key = ""
            channel.hls_playback_url = ""
            channel.save(
                update_fields=[
                    "live_input_uid",
                    "rtmps_url",
                    "rtmps_key",
                    "hls_playback_url",
                    "updated_at",
                ]
            )
            done += 1
        label = "déprovisionnée(s)" if apply else "à déprovisionner (dry-run)"
        self.stdout.write(self.style.SUCCESS(f"{done} chaîne(s) {label}."))
