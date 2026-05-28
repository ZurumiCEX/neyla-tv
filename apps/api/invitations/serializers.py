from __future__ import annotations

from rest_framework import serializers

from .models import Invite


class InviteSerializer(serializers.ModelSerializer):
    is_usable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Invite
        fields = ("code", "max_uses", "used_count", "is_usable", "expires_at", "created_at")
        read_only_fields = fields


class InviteCreateSerializer(serializers.Serializer):
    max_uses = serializers.IntegerField(min_value=1, max_value=1000, required=False, default=1)
