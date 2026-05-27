from __future__ import annotations

from rest_framework import serializers

from .models import Report


class ReportCreateSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=Report.Reason.choices)
    target_username = serializers.CharField(required=False, allow_blank=True, default="")
    channel_slug = serializers.CharField(required=False, allow_blank=True, default="")
    message_id = serializers.CharField(required=False, allow_blank=True, default="")
    details = serializers.CharField(required=False, allow_blank=True, default="", max_length=1000)
