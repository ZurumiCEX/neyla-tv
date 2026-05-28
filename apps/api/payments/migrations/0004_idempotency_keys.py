"""Clés d'idempotence sur Purchase/Tip/Payout — écrite à la main."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0003_feerule_ledger_meta"),
    ]

    operations = [
        migrations.AddField(
            model_name="purchase",
            name="idempotency_key",
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="tip",
            name="idempotency_key",
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="payout",
            name="idempotency_key",
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
    ]
