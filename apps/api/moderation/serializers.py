from __future__ import annotations

from rest_framework import serializers

from .models import Report


class ReportCreateSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=Report.Reason.choices)
    target_username = serializers.CharField(required=False, allow_blank=True, default="")
    channel_slug = serializers.CharField(required=False, allow_blank=True, default="")
    message_id = serializers.CharField(required=False, allow_blank=True, default="")
    details = serializers.CharField(required=False, allow_blank=True, default="", max_length=1000)


class ReportSerializer(serializers.ModelSerializer):
    reporter = serializers.CharField(source="reporter.username", read_only=True)
    target_user = serializers.CharField(source="target_user.username", read_only=True, default=None)
    channel = serializers.CharField(source="channel.slug", read_only=True, default=None)
    assigned_to = serializers.CharField(source="assigned_to.username", read_only=True, default=None)

    class Meta:
        model = Report
        fields = (
            "id",
            "reason",
            "status",
            "reporter",
            "target_user",
            "channel",
            "message_id",
            "details",
            "assigned_to",
            "resolution",
            "resolved_at",
            "created_at",
        )
        read_only_fields = fields


class ReportUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Report.Status.choices, required=False, default="")
    resolution = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=1000
    )
    assign_to_self = serializers.BooleanField(required=False, default=False)
    ban = serializers.BooleanField(required=False, default=False)


class BannedWordImportSerializer(serializers.Serializer):
    words = serializers.CharField(allow_blank=False)
