"""Jeton overlay d'alertes sur Channel (écrite à la main)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("channels_app", "0005_channel_tags"),
    ]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="overlay_token",
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
    ]
