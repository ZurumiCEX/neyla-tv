"""Ajoute le type de ledger ADJUSTMENT (ajustement admin, écrite à la main)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0006_ledger_referral"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ledgerentry",
            name="kind",
            field=models.CharField(
                choices=[
                    ("purchase", "Achat"),
                    ("tip_sent", "Tip envoyé"),
                    ("tip_received", "Tip reçu"),
                    ("sub_paid", "Abonnement payé"),
                    ("sub_earned", "Abonnement reçu"),
                    ("payout", "Retrait"),
                    ("referral", "Parrainage"),
                    ("adjustment", "Ajustement admin"),
                ],
                max_length=16,
            ),
        ),
    ]
