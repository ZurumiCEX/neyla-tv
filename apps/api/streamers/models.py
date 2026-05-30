"""Candidature streamer — « Creator Application System ».

Un inscrit dépose une candidature détaillée (identité, profil gaming, motivation,
expérience, équipement, personnalité). Un score automatique aide l'admin à
prioriser. Le provisioning Cloudflare n'a lieu qu'à l'approbation (cf. services).
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


class ContentCategory(models.TextChoices):
    GAMING = "gaming", "Gaming"
    JUST_CHATTING = "just_chatting", "Just Chatting"
    ESPORTS = "esports", "Esports"
    MOBILE = "mobile", "Mobile Gaming"
    IRL = "irl", "IRL"
    CREATIVE = "creative", "Créatif"


class Goal(models.TextChoices):
    COMMUNITY = "community", "Construire une communauté"
    ENTERTAIN = "entertain", "Divertir"
    PRO = "pro", "Devenir créateur pro"
    ESPORT = "esport", "Participer à l'esport"
    REVENUE = "revenue", "Gagner des revenus"
    PASSION = "passion", "Partager ma passion gaming"


class CommunitySize(models.TextChoices):
    NONE = "none", "Débutant"
    UNDER_100 = "under_100", "< 100 abonnés"
    K1 = "100_1k", "100 – 1k"
    K10 = "1k_10k", "1k – 10k"
    K10_PLUS = "10k_plus", "10k+"


class Frequency(models.TextChoices):
    OCCASIONAL = "occasional", "Occasionnel"
    WEEK_1_2 = "1_2_week", "1–2 fois/semaine"
    WEEK_3_5 = "3_5_week", "3–5 fois/semaine"
    DAILY = "daily", "Quotidien"


class Duration(models.TextChoices):
    UNDER_1H = "under_1h", "< 1h"
    H1_3 = "1_3h", "1–3h"
    H3_5 = "3_5h", "3–5h"
    H5_PLUS = "5h_plus", "5h+"


class SetupItem(models.TextChoices):
    PC = "pc", "PC Gaming"
    CONSOLE = "console", "Console"
    MOBILE = "mobile", "Mobile"
    WEBCAM = "webcam", "Webcam"
    MICROPHONE = "microphone", "Microphone"
    STABLE_NET = "stable_net", "Fibre/Wifi stable"


class ConnectionQuality(models.TextChoices):
    LOW = "low", "Faible"
    MEDIUM = "medium", "Moyenne"
    GOOD = "good", "Bonne"
    EXCELLENT = "excellent", "Excellente"


class CommunityType(models.TextChoices):
    FUN = "fun", "Fun"
    COMPETITIVE = "competitive", "Compétitive"
    CHILL = "chill", "Chill"
    EDUCATIONAL = "educational", "Éducative"
    ESPORT = "esport", "Esport"
    AFRICAN = "african", "Africaine"
    INCLUSIVE = "inclusive", "Inclusive"


class StreamerApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        UNDER_REVIEW = "under_review", "En cours d'examen"
        INTERVIEW = "interview", "Entretien demandé"
        APPROVED = "approved", "Approuvée"
        REJECTED = "rejected", "Rejetée"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="streamer_application",
    )
    status = models.CharField(
        max_length=14, choices=Status.choices, default=Status.PENDING, db_index=True
    )

    # 1. Identité streamer
    full_name = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=2, blank=True)  # ISO-3166-1 alpha-2
    primary_language = models.CharField(max_length=40, blank=True)

    # 2. Profil gaming
    main_games = models.CharField(max_length=200, blank=True)
    content_categories = models.JSONField(default=list, blank=True)

    # 3. Motivation & vision
    motivation = models.TextField(max_length=2000, blank=True)
    goals = models.JSONField(default=list, blank=True)
    community_type = models.JSONField(default=list, blank=True)

    # 4. Expérience créateur
    has_streamed = models.BooleanField(default=False)
    platforms = models.JSONField(default=dict, blank=True)  # {twitch, youtube, …}
    community_size = models.CharField(max_length=12, blank=True)

    # 5. Qualité & régularité
    frequency = models.CharField(max_length=12, blank=True)
    avg_duration = models.CharField(max_length=12, blank=True)

    # 6. Équipement
    setup = models.JSONField(default=list, blank=True)
    connection_quality = models.CharField(max_length=12, blank=True)

    # 7. Signaux forts
    why_select = models.TextField(max_length=1000, blank=True)
    what_bring = models.TextField(max_length=1000, blank=True)

    # 8. Bonus
    intro_video_url = models.URLField(blank=True)
    setup_screenshot_url = models.URLField(blank=True)

    # Engagement règles
    rules_accepted = models.BooleanField(default=False)

    # 9. Scoring + back-office
    score = models.PositiveIntegerField(default=0, db_index=True)
    admin_notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="streamer_decisions",
    )
    rejection_reason = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-score", "-created_at"]

    def __str__(self) -> str:
        return f"{self.user} ({self.status}, {self.score})"
