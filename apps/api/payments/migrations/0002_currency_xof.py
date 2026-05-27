"""Devise par défaut XOF (FCFA) sur Purchase et Payout — écrite à la main."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="purchase",
            name="currency",
            field=models.CharField(default="XOF", max_length=8),
        ),
        migrations.AlterField(
            model_name="payout",
            name="currency",
            field=models.CharField(default="XOF", max_length=8),
        ),
    ]
