"""Pays + liens sociaux sur User (écrite à la main)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_user_invited_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="country",
            field=models.CharField(blank=True, max_length=2),
        ),
        migrations.AddField(
            model_name="user",
            name="social_links",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
