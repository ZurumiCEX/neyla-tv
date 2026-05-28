"""Parrainage : lien invited_by (auto-référence User) — écrite à la main."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_user_role"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="invited_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="invited_users",
                to="accounts.user",
            ),
        ),
    ]
