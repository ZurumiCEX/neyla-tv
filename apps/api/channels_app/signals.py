"""Création automatique d'une Channel à l'inscription d'un User."""

from __future__ import annotations

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Channel
from .tasks import provision_live_input_task


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_channel_for_new_user(sender, instance, created, **kwargs):  # noqa: ARG001
    if not created:
        return
    channel, was_created = Channel.objects.get_or_create(
        user=instance,
        defaults={"slug": instance.username},
    )
    if was_created:
        provision_live_input_task.delay(channel.pk)
