from __future__ import annotations

from rest_framework import serializers

from .models import StreamerApplication


class StreamerApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamerApplication
        fields = ("status", "motivation", "created_at", "decided_at", "rejection_reason")
        read_only_fields = fields
