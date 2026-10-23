"""Passage à Bunny Stream : champs fournisseur neutres (écrite à la main)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("channels_app", "0007_channel_collaborations_open"),
    ]

    operations = [
        migrations.RenameField("channel", "live_input_uid", "stream_id"),
        migrations.RenameField("channel", "rtmps_url", "ingest_url"),
        migrations.RenameField("channel", "rtmps_key", "stream_key"),
        migrations.RenameField("channel", "hls_playback_url", "playback_url"),
        migrations.AddField(
            model_name="channel",
            name="stream_checked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
