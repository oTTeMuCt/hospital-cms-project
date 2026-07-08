from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    content_type_name = serializers.CharField(
        source="target_content_type.model", read_only=True
    )

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "user_name",
            "action",
            "target_content_type",
            "content_type_name",
            "target_object_id",
            "ip_address",
            "user_agent",
            "succeeded",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.full_name_display or obj.user.username
        return None
