from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class NotificationChannel(models.TextChoices):
    TELEGRAM = "telegram", "Telegram"
    SMS = "sms", "SMS"
    EMAIL = "email", "Email"
    PUSH = "push", "Push"


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"


class Notification(models.Model):
    recipient_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="notification_recipients")
    recipient_object_id = models.PositiveBigIntegerField()
    recipient = GenericForeignKey("recipient_content_type", "recipient_object_id")
    channel = models.CharField(max_length=32, choices=NotificationChannel.choices)
    subject = models.CharField(max_length=255, blank=True)
    text = models.TextField()
    status = models.CharField(max_length=32, choices=NotificationStatus.choices, default=NotificationStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_notifications",
    )

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_channel_display()} notification to {self.recipient}"
