from __future__ import annotations

from rest_framework import serializers

from .models import Charity, CharityEvent, PlatformEvent


class CharitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Charity
        fields = ("slug", "name", "description", "country", "logo_url", "website_url")
        read_only_fields = fields


class CharityEventSerializer(serializers.ModelSerializer):
    beneficiaries = CharitySerializer(many=True, read_only=True)
    is_open = serializers.BooleanField(read_only=True)

    class Meta:
        model = CharityEvent
        fields = (
            "slug",
            "title",
            "theme",
            "description_md",
            "cover_url",
            "starts_at",
            "ends_at",
            "floor_aura",
            "is_published",
            "is_open",
            "beneficiaries",
            "total_aura_cached",
        )
        read_only_fields = fields


class PlatformEventSerializer(serializers.ModelSerializer):
    is_ongoing = serializers.BooleanField(read_only=True)

    class Meta:
        model = PlatformEvent
        fields = (
            "slug",
            "title",
            "kind",
            "description_md",
            "cover_url",
            "link_url",
            "starts_at",
            "ends_at",
            "is_published",
            "is_ongoing",
            "featured",
        )
        read_only_fields = fields


class DonateWriteSerializer(serializers.Serializer):
    event_slug = serializers.SlugField(max_length=80)
    charity_slug = serializers.SlugField(max_length=80)
    aura_amount = serializers.IntegerField(min_value=1, max_value=10_000_000)
    message = serializers.CharField(max_length=140, required=False, allow_blank=True, default="")
    anonymous = serializers.BooleanField(required=False, default=False)
