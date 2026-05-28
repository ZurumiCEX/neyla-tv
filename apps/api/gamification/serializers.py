from __future__ import annotations

from rest_framework import serializers

from .models import Achievement


class AchievementSerializer(serializers.ModelSerializer):
    unlocked = serializers.SerializerMethodField()
    awarded_at = serializers.SerializerMethodField()

    class Meta:
        model = Achievement
        fields = ("key", "name", "description", "icon", "order", "unlocked", "awarded_at")

    def get_unlocked(self, obj) -> bool:
        return obj.key in self.context.get("unlocked_map", {})

    def get_awarded_at(self, obj):
        return self.context.get("unlocked_map", {}).get(obj.key)
