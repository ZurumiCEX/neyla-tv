"""Monétisation v2 (écrite à la main) :

- `PlatformRevenue` : trace de chaque commission plateforme ;
- `IdempotencyRecord` : idempotence générique (abonnements…) ;
- clés d'idempotence scopées par utilisateur (Purchase, Tip, Payout) ;
- remboursements / litiges d'achat, gel des retraits, destination mobile money ;
- types de ledger `payout_reversal` et `refund`.

Données : les remboursements de retrait historiques (écritures `payout`
positives) deviennent `payout_reversal` ; les commissions des tips existants
sont reprises dans `PlatformRevenue`.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

DESTINATIONS = [("wave", "Wave"), ("orange_money", "Orange Money")]


def forwards(apps, schema_editor):
    LedgerEntry = apps.get_model("payments", "LedgerEntry")
    Tip = apps.get_model("payments", "Tip")
    PlatformRevenue = apps.get_model("payments", "PlatformRevenue")
    LedgerEntry.objects.filter(kind="payout", amount__gt=0).update(kind="payout_reversal")
    PlatformRevenue.objects.bulk_create(
        [
            PlatformRevenue(
                source="tip",
                amount_aura=t.platform_fee,
                user_id=t.from_user_id,
                related_type="tip",
                related_id=t.id,
            )
            for t in Tip.objects.filter(platform_fee__gt=0).iterator()
        ],
        batch_size=500,
    )


def backwards(apps, schema_editor):
    LedgerEntry = apps.get_model("payments", "LedgerEntry")
    LedgerEntry.objects.filter(kind="payout_reversal").update(kind="payout")


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0009_ledger_charity_kind"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PlatformRevenue",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("tip", "Tip"),
                            ("subscription", "Abonnement"),
                            ("purchase", "Achat (streamer)"),
                            ("withdrawal", "Frais de retrait"),
                        ],
                        db_index=True,
                        max_length=16,
                    ),
                ),
                ("amount_aura", models.PositiveIntegerField()),
                ("related_type", models.CharField(blank=True, max_length=32)),
                ("related_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        help_text="Utilisateur à l'origine du flux (payeur ou créateur qui retire).",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="IdempotencyRecord",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False),
                ),
                ("scope", models.CharField(max_length=32)),
                ("key", models.CharField(max_length=64)),
                ("object_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="idempotency_records",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="idempotencyrecord",
            constraint=models.UniqueConstraint(
                fields=("user", "scope", "key"), name="uniq_idempotency_record"
            ),
        ),
        # --- Wallet : gel des retraits ---
        migrations.AddField(
            model_name="wallet",
            name="payout_hold",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="wallet",
            name="payout_hold_reason",
            field=models.CharField(blank=True, max_length=255),
        ),
        # --- Ledger : nouveaux types ---
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
                    ("payout_reversal", "Retrait annulé"),
                    ("referral", "Parrainage"),
                    ("adjustment", "Ajustement admin"),
                    ("charity_donation", "Don caritatif"),
                    ("refund", "Remboursement d'achat"),
                ],
                max_length=16,
            ),
        ),
        # --- Purchase : remboursements / litiges + clé par utilisateur ---
        migrations.AddField(
            model_name="purchase",
            name="provider_payment_ref",
            field=models.CharField(blank=True, db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name="purchase",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "En attente"),
                    ("paid", "Payé"),
                    ("failed", "Échoué"),
                    ("refunded", "Remboursé"),
                    ("disputed", "Contesté"),
                ],
                db_index=True,
                default="pending",
                max_length=8,
            ),
        ),
        migrations.AlterField(
            model_name="purchase",
            name="idempotency_key",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddConstraint(
            model_name="purchase",
            constraint=models.UniqueConstraint(
                condition=models.Q(idempotency_key__isnull=False),
                fields=("user", "idempotency_key"),
                name="uniq_purchase_user_idem",
            ),
        ),
        # --- Tip : clé par utilisateur ---
        migrations.AlterField(
            model_name="tip",
            name="idempotency_key",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddConstraint(
            model_name="tip",
            constraint=models.UniqueConstraint(
                condition=models.Q(idempotency_key__isnull=False),
                fields=("from_user", "idempotency_key"),
                name="uniq_tip_user_idem",
            ),
        ),
        # --- Retraits : destination mobile money, frais, statut « en cours » ---
        migrations.AddField(
            model_name="payoutotp",
            name="destination_provider",
            field=models.CharField(blank=True, choices=DESTINATIONS, max_length=16),
        ),
        migrations.AddField(
            model_name="payoutotp",
            name="destination_phone",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="payout",
            name="fee_aura",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="payout",
            name="destination_provider",
            field=models.CharField(blank=True, choices=DESTINATIONS, max_length=16),
        ),
        migrations.AddField(
            model_name="payout",
            name="destination_phone",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="payout",
            name="resolved_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="payout",
            name="status",
            field=models.CharField(
                choices=[
                    ("requested", "Demandé"),
                    ("processing", "En cours de versement"),
                    ("paid", "Payé"),
                    ("failed", "Échoué"),
                ],
                db_index=True,
                default="requested",
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="payout",
            name="idempotency_key",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddConstraint(
            model_name="payout",
            constraint=models.UniqueConstraint(
                condition=models.Q(idempotency_key__isnull=False),
                fields=("user", "idempotency_key"),
                name="uniq_payout_user_idem",
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
