"""Miroir : tout CharityEvent publié apparaît dans le calendrier PlatformEvent."""

from __future__ import annotations

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import CharityEvent, PlatformEvent


@receiver(post_save, sender=CharityEvent)
def mirror_charity_into_platform_event(sender, instance: CharityEvent, **kwargs):
    """Crée/met à jour un PlatformEvent miroir pour le calendrier header."""
    PlatformEvent.objects.update_or_create(
        slug=f"charity-{instance.slug}",
        defaults={
            "title": instance.title,
            "kind": PlatformEvent.Kind.CHARITY,
            "description_md": instance.description_md,
            "cover_url": instance.cover_url,
            "link_url": f"/charity/{instance.slug}",
            "starts_at": instance.starts_at,
            "ends_at": instance.ends_at,
            "is_published": instance.is_published,
            "featured": True,
        },
    )


@receiver(post_delete, sender=CharityEvent)
def cleanup_mirrored_event(sender, instance: CharityEvent, **kwargs):
    PlatformEvent.objects.filter(slug=f"charity-{instance.slug}").delete()
