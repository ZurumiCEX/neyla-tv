"""Passkeys (WebAuthn), anti-rejeu TOTP, secret TOTP chiffré au repos — écrite à la main."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def encrypt_secrets(apps, schema_editor):
    from accounts.crypto import encrypt

    TwoFactor = apps.get_model("accounts", "TwoFactor")
    for tf in TwoFactor.objects.all():
        if tf.secret and not tf.secret.startswith("enc:"):
            tf.secret = encrypt(tf.secret)
            tf.save(update_fields=["secret"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0014_user_lifetime_aura_spent"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="twofactor",
            name="secret",
            field=models.CharField(max_length=255),
        ),
        migrations.AddField(
            model_name="twofactor",
            name="last_used_step",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(encrypt_secrets, migrations.RunPython.noop),
        migrations.CreateModel(
            name="Passkey",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("credential_id", models.CharField(max_length=512, unique=True)),
                ("public_key", models.TextField()),
                ("sign_count", models.PositiveBigIntegerField(default=0)),
                ("transports", models.JSONField(blank=True, default=list)),
                ("name", models.CharField(default="Passkey", max_length=60)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="passkeys",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
