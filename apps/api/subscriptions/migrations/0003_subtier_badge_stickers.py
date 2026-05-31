"""Avantages d'abonnement : badge + stickers (écrite à la main)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0002_gifted_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="subtier",
            name="badge_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="subtier",
            name="stickers_urls",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
