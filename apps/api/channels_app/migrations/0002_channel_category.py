"""Ajoute la catégorie (FK Game) sur Channel."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("channels_app", "0001_initial"),
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="channels",
                to="catalog.game",
            ),
        ),
    ]
