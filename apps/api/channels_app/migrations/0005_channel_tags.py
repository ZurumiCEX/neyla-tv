"""Tags de découverte sur Channel (écrite à la main)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("channels_app", "0004_channel_banner_socials"),
    ]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="tags",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
