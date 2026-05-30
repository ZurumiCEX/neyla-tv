from __future__ import annotations

from rest_framework import serializers

from .models import (
    CommunitySize,
    CommunityType,
    ConnectionQuality,
    ContentCategory,
    Duration,
    Frequency,
    Goal,
    SetupItem,
    StreamerApplication,
)

_PLATFORM_KEYS = {"twitch", "youtube", "tiktok", "kick", "facebook", "discord"}


def _choices_list(enum):
    return serializers.ListField(
        child=serializers.ChoiceField(choices=enum.choices),
        required=False,
        default=list,
    )


class StreamerApplicationWriteSerializer(serializers.Serializer):
    """Valide la candidature « Creator Application System » (entrée API)."""

    # 1. Identité
    full_name = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    country = serializers.CharField(max_length=2, required=False, allow_blank=True, default="")
    primary_language = serializers.CharField(
        max_length=40, required=False, allow_blank=True, default=""
    )

    # 2. Profil gaming
    main_games = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    content_categories = _choices_list(ContentCategory)

    # 3. Motivation & vision
    motivation = serializers.CharField(
        max_length=2000, required=False, allow_blank=True, default=""
    )
    goals = _choices_list(Goal)
    community_type = _choices_list(CommunityType)

    # 4. Expérience
    has_streamed = serializers.BooleanField(required=False, default=False)
    platforms = serializers.DictField(
        child=serializers.CharField(max_length=200, allow_blank=True),
        required=False,
        default=dict,
    )
    community_size = serializers.ChoiceField(
        choices=CommunitySize.choices, required=False, allow_blank=True, default=""
    )

    # 5. Qualité & régularité
    frequency = serializers.ChoiceField(
        choices=Frequency.choices, required=False, allow_blank=True, default=""
    )
    avg_duration = serializers.ChoiceField(
        choices=Duration.choices, required=False, allow_blank=True, default=""
    )

    # 6. Équipement
    setup = _choices_list(SetupItem)
    connection_quality = serializers.ChoiceField(
        choices=ConnectionQuality.choices, required=False, allow_blank=True, default=""
    )

    # 7. Signaux forts
    why_select = serializers.CharField(
        max_length=1000, required=False, allow_blank=True, default=""
    )
    what_bring = serializers.CharField(
        max_length=1000, required=False, allow_blank=True, default=""
    )

    # 8. Bonus
    intro_video_url = serializers.URLField(required=False, allow_blank=True, default="")
    setup_screenshot_url = serializers.URLField(required=False, allow_blank=True, default="")

    # Engagement règles (obligatoire)
    rules_accepted = serializers.BooleanField()

    def validate_rules_accepted(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError(
                "Tu dois accepter les règles et standards de Neyla pour candidater."
            )
        return value

    def validate_platforms(self, value: dict) -> dict:
        cleaned = {}
        for key, link in value.items():
            if key not in _PLATFORM_KEYS:
                raise serializers.ValidationError(f"Plateforme non supportée : {key}.")
            if link:
                cleaned[key] = link
        return cleaned

    def validate_country(self, value: str) -> str:
        value = (value or "").strip().upper()
        if value and len(value) != 2:
            raise serializers.ValidationError("Code pays ISO à 2 lettres attendu.")
        return value


class StreamerApplicationSerializer(serializers.ModelSerializer):
    """Vue renvoyée au candidat (statut + écho des champs pour préremplir)."""

    class Meta:
        model = StreamerApplication
        fields = (
            "status",
            "score",
            "motivation",
            "full_name",
            "country",
            "primary_language",
            "main_games",
            "content_categories",
            "goals",
            "community_type",
            "has_streamed",
            "platforms",
            "community_size",
            "frequency",
            "avg_duration",
            "setup",
            "connection_quality",
            "why_select",
            "what_bring",
            "intro_video_url",
            "setup_screenshot_url",
            "created_at",
            "decided_at",
            "rejection_reason",
        )
        read_only_fields = fields
