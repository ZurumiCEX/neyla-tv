"""Ajoute le type de ledger CHARITY_DONATION (écrite à la main)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0008_seed_default_fees"),
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
                    ("charity_donation", "Don caritatif"),
                ],
                max_length=16,
            ),
        ),
    ]
