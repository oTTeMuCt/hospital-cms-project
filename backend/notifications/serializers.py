from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import Notification

User = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient_content_type",
            "recipient_object_id",
            "recipient",
            "channel",
            "subject",
            "text",
            "status",
            "created_at",
            "sent_at",
            "error_message",
            "created_by",
        ]
        read_only_fields = ["id", "created_at", "sent_at", "status"]
