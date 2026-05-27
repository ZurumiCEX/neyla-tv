"""Migration initiale monétisation Aura (écrite à la main)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("channels_app", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Wallet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("aura_balance", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wallet",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Purchase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("credits", models.PositiveIntegerField()),
                ("fiat_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("currency", models.CharField(default="EUR", max_length=8)),
                ("provider", models.CharField(max_length=20)),
                ("provider_ref", models.CharField(blank=True, max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "En attente"), ("paid", "Payé"), ("failed", "Échoué")],
                        db_index=True,
                        default="pending",
                        max_length=8,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="purchases",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Payout",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("aura_amount", models.PositiveIntegerField()),
                ("fiat_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("currency", models.CharField(default="EUR", max_length=8)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("requested", "Demandé"),
                            ("paid", "Payé"),
                            ("failed", "Échoué"),
                        ],
                        db_index=True,
                        default="requested",
                        max_length=10,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payouts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Tip",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("aura_amount", models.PositiveIntegerField()),
                ("creator_share", models.PositiveIntegerField()),
                ("platform_fee", models.PositiveIntegerField()),
                ("message", models.CharField(blank=True, max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "from_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tips_sent",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "to_channel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tips",
                        to="channels_app.channel",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="LedgerEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("amount", models.IntegerField()),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("purchase", "Achat"),
                            ("tip_sent", "Tip envoyé"),
                            ("tip_received", "Tip reçu"),
                            ("payout", "Retrait"),
                        ],
                        max_length=16,
                    ),
                ),
                ("reference", models.CharField(blank=True, max_length=255)),
                ("balance_after", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "wallet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="entries",
                        to="payments.wallet",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
