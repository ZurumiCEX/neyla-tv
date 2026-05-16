"""Migration initiale du modèle Follow."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Follow",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "follower",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="following",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "followee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="followers",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="follow",
            index=models.Index(fields=["follower"], name="social_foll_followe_b3ce8c_idx"),
        ),
        migrations.AddIndex(
            model_name="follow",
            index=models.Index(fields=["followee"], name="social_foll_followe_4d56fb_idx"),
        ),
        migrations.AddConstraint(
            model_name="follow",
            constraint=models.UniqueConstraint(fields=("follower", "followee"), name="uniq_follow"),
        ),
    ]
