"""Versements effectifs aux associations (transparence « versé / en attente »)."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("charity", "0003_fix_charity_link_url"),
    ]

    operations = [
        migrations.CreateModel(
            name="CharityDisbursement",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False),
                ),
                (
                    "aura_amount",
                    models.PositiveIntegerField(help_text="Aura couverts par ce versement."),
                ),
                (
                    "fiat_amount_xof",
                    models.PositiveIntegerField(help_text="Montant versé en FCFA."),
                ),
                (
                    "reference",
                    models.CharField(help_text="Référence du virement / reçu.", max_length=120),
                ),
                ("paid_at", models.DateField()),
                (
                    "proof_url",
                    models.URLField(blank=True, help_text="Reçu ou attestation (optionnel)."),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "charity",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="disbursements",
                        to="charity.charity",
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="disbursements",
                        to="charity.charityevent",
                    ),
                ),
            ],
            options={"ordering": ["-paid_at", "-created_at"]},
        ),
    ]
