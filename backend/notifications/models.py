from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class NotificationChannel(models.TextChoices):
    TELEGRAM = "telegram", "Telegram"
    SMS = "sms", "SMS"
    EMAIL = "email", "Email"
    PUSH = "push", "Push-уведомление"


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Ожидает отправки"
    SENT = "sent", "Отправлено"
    FAILED = "failed", "Ошибка отправки"


class Notification(models.Model):
    recipient_content_type = models.ForeignKey(
        ContentType,
        verbose_name="Тип получателя",
        on_delete=models.CASCADE,
        related_name="notification_recipients",
    )
    recipient_object_id = models.PositiveBigIntegerField("ID получателя")
    recipient = GenericForeignKey("recipient_content_type", "recipient_object_id")
    channel = models.CharField(
        "Канал связи",
        max_length=32,
        choices=NotificationChannel.choices,
    )
    subject = models.CharField("Тема", max_length=255, blank=True)
    text = models.TextField("Текст уведомления")
    status = models.CharField(
        "Статус",
        max_length=32,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    sent_at = models.DateTimeField("Дата отправки", null=True, blank=True)
    error_message = models.TextField("Ошибка", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Инициатор",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_notifications",
    )

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_channel_display()}: {self.subject or self.text[:50]}"
