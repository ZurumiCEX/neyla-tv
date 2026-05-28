from __future__ import annotations

from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "type", "payload", "read_at", "created_at")
        read_only_fields = fields


class SupportMessageSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30)
    title = serializers.CharField(max_length=120)
    body = serializers.CharField(max_length=2000)
