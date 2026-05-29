"""Drapeau d'ouverture des collaborations (écrite à la main)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("channels_app", "0006_channel_overlay_token"),
    ]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="collaborations_open",
            field=models.BooleanField(default=True),
        ),
    ]
