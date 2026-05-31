"""Module Charity Day : événements caritatifs mensuels + dons en Aura.

Différenciateur RSE de la plateforme : 1 événement par mois pendant lequel les
streamers sont invités à reverser une partie de leurs revenus à une association
agréée. Tous les dons sont en Aura, transparents et listés publiquement.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class Charity(models.Model):
    """Association/institution agréée par l'admin (KYC manuel)."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    country = models.CharField(
        max_length=2, blank=True, help_text="Code pays ISO-3166-1 alpha-2 (ex. SN, CI, BF)."
    )
    logo_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    is_active = models.BooleanField(
        default=True, db_index=True, help_text="Décocher pour masquer du catalogue."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Association"
        verbose_name_plural = "Associations"

    def __str__(self) -> str:  # pragma: no cover - cosmétique
        return self.name


class CharityEvent(models.Model):
    """Charity Day : 1 événement par mois, agréé et publié par l'admin."""

    slug = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=140)
    theme = models.CharField(max_length=80, blank=True, help_text="Thème mensuel.")
    description_md = models.TextField(blank=True, help_text="Markdown autorisé.")
    cover_url = models.URLField(blank=True)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(db_index=True)
    floor_aura = models.PositiveIntegerField(default=10, help_text="Don minimal recommandé (Aura).")
    is_published = models.BooleanField(default=True, db_index=True)
    beneficiaries = models.ManyToManyField(
        Charity, related_name="events", help_text="Associations bénéficiaires."
    )
    total_aura_cached = models.PositiveBigIntegerField(
        default=0, help_text="Total Aura collecté (mis à jour à chaque don, lecture rapide)."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-starts_at"]
        verbose_name = "Charity Day"
        verbose_name_plural = "Charity Days"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.title} ({self.starts_at:%Y-%m-%d})"

    @property
    def is_open(self) -> bool:
        """Fenêtre de don ouverte (publié + dans la plage horaire)."""
        if not self.is_published:
            return False
        now = timezone.now()
        return self.starts_at <= now <= self.ends_at


class PlatformEvent(models.Model):
    """Événement de plateforme affiché dans le calendrier header.

    Catalogue généraliste (tournois, premières, annonces…). Un `CharityEvent`
    est miroir-promu automatiquement ici (signal post_save) avec `kind=charity`.
    """

    class Kind(models.TextChoices):
        CHARITY = "charity", "Charity Day"
        TOURNAMENT = "tournament", "Tournoi"
        PREMIERE = "premiere", "Première"
        ANNOUNCEMENT = "announcement", "Annonce"
        MAINTENANCE = "maintenance", "Maintenance"

    slug = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=140)
    kind = models.CharField(
        max_length=20, choices=Kind.choices, default=Kind.ANNOUNCEMENT, db_index=True
    )
    description_md = models.TextField(blank=True)
    cover_url = models.URLField(blank=True)
    link_url = models.URLField(blank=True, help_text="Lien interne ou externe.")
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(db_index=True)
    is_published = models.BooleanField(default=True, db_index=True)
    featured = models.BooleanField(default=False, help_text="Mettre en avant dans le menu.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at"]
        verbose_name = "Événement plateforme"
        verbose_name_plural = "Événements plateforme"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.title} [{self.kind}] {self.starts_at:%Y-%m-%d}"

    @property
    def is_ongoing(self) -> bool:
        now = timezone.now()
        return self.is_published and self.starts_at <= now <= self.ends_at


class CharityDonation(models.Model):
    """Don d'un utilisateur à une association pendant un événement."""

    event = models.ForeignKey(CharityEvent, on_delete=models.CASCADE, related_name="donations")
    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="charity_donations"
    )
    charity = models.ForeignKey(Charity, on_delete=models.PROTECT, related_name="donations")
    aura_amount = models.PositiveIntegerField()
    message = models.CharField(max_length=140, blank=True)
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            # Leaderboard rapide par événement (par montant décroissant).
            models.Index(fields=["event", "-aura_amount"], name="charity_event_lb_idx"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.donor_id}->{self.charity_id}:{self.aura_amount}"
