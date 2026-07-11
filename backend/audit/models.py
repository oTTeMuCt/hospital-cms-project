from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField("Действие", max_length=255)
    target_content_type = models.ForeignKey(
        ContentType,
        verbose_name="Тип объекта",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    target_object_id = models.PositiveBigIntegerField("ID объекта", null=True, blank=True)
    target = GenericForeignKey("target_content_type", "target_object_id")
    ip_address = models.GenericIPAddressField("IP-адрес", null=True, blank=True)
    user_agent = models.CharField("User-Agent", max_length=512, blank=True)
    succeeded = models.BooleanField("Успешно", default=True)
    metadata = models.JSONField("Метаданные", blank=True, null=True)
    created_at = models.DateTimeField("Дата и время", auto_now_add=True)

    class Meta:
        verbose_name = "Запись журнала аудита"
        verbose_name_plural = "Журнал аудита"
        ordering = ["-created_at"]

    def __str__(self):
        user_str = self.user.get_full_name() if self.user else "Аноним"
        return f"[{self.created_at:%d.%m.%Y %H:%M}] {user_str} — {self.action}"
