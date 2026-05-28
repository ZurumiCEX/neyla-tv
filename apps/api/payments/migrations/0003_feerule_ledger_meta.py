"""Enrichissement ledger (currency/related/metadata) + règles de commission — à la main."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0002_currency_xof"),
    ]

    operations = [
        migrations.AddField(
            model_name="ledgerentry",
            name="currency",
            field=models.CharField(default="AURA", max_length=8),
        ),
        migrations.AddField(
            model_name="ledgerentry",
            name="related_type",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="ledgerentry",
            name="related_id",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="ledgerentry",
            name="metadata",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.CreateModel(
            name="FeeRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                (
                    "product",
                    models.CharField(
                        choices=[
                            ("tip", "Tip"),
                            ("subscription", "Abonnement"),
                            ("purchase", "Achat"),
                        ],
                        db_index=True,
                        max_length=16,
                    ),
                ),
                (
                    "mode",
                    models.CharField(
                        choices=[("percentage", "Pourcentage"), ("fixed", "Montant fixe")],
                        default="percentage",
                        max_length=12,
                    ),
                ),
                ("value", models.DecimalField(decimal_places=2, max_digits=9)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["product", "-created_at"]},
        ),
    ]
