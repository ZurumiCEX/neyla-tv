from __future__ import annotations

from rest_framework import serializers

from .models import Game


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ("slug", "name", "box_art_url")


class GameWithCountSerializer(GameSerializer):
    live_count = serializers.IntegerField(read_only=True)

    class Meta(GameSerializer.Meta):
        fields = GameSerializer.Meta.fields + ("live_count",)
