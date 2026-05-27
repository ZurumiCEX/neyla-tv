"""Bannière + réseaux sociaux sur Channel (écrite à la main)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("channels_app", "0003_streamsession"),
    ]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="banner_url",
            field=models.URLField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="channel",
            name="social_links",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
