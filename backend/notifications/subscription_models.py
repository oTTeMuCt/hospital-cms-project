"""
Subscription model to replace JSON file storage.

This replaces bot/subscriptions.json with proper database persistence
so subscriptions survive restarts and can be managed via admin.
"""
import json
import logging
import os
from pathlib import Path

from django.conf import settings
from django.db import models

from patients.models import Patient

logger = logging.getLogger("notifications.subscriptions")


class Subscription(models.Model):
    """
    Stores Telegram chat subscriptions to patient notifications.
    Replaces the bot/subscriptions.json file storage.
    """
    chat_id = models.BigIntegerField(
        "Telegram Chat ID",
        unique=True,
        help_text="Уникальный идентификатор чата Telegram",
    )
    patient = models.ForeignKey(
        Patient,
        verbose_name="Пациент",
        on_delete=models.CASCADE,
        related_name="subscriptions",
        null=True,
        blank=True,
    )
    patient_id_str = models.CharField(
        "ID пациента (строка)",
        max_length=32,
        blank=True,
        help_text="ID пациента в формате '1' или 'P-000001' (для обратной совместимости)",
    )
    is_active = models.BooleanField("Активна", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Подписка Telegram"
        verbose_name_plural = "Подписки Telegram"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["chat_id"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        patient_info = f" — {self.patient}" if self.patient else f" (ID: {self.patient_id_str})"
        return f"Chat {self.chat_id}{patient_info}"


def import_subscriptions_from_json(json_path=None):
    """
    Import subscriptions from the legacy JSON file into the database.
    Call this once during migration to migrate existing data.
    """
    if json_path is None:
        json_path = Path(settings.BASE_DIR).parent / "bot" / "subscriptions.json"

    if not os.path.exists(json_path):
        logger.info("No subscriptions.json found at %s — skipping import.", json_path)
        return 0

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to read subscriptions.json: %s", exc)
        return 0

    imported = 0
    for chat_id_str, patient_id_str in data.items():
        try:
            chat_id = int(chat_id_str)
            sub, created = Subscription.objects.get_or_create(
                chat_id=chat_id,
                defaults={"patient_id_str": patient_id_str},
            )
            if created:
                # Try to link to actual patient record
                from patients.models import Patient
                cleaned = patient_id_str.strip()
                try:
                    patient_id = int(cleaned.lstrip("0"))
                    patient = Patient.objects.filter(pk=patient_id).first()
                    if patient:
                        sub.patient = patient
                        sub.save(update_fields=["patient"])
                except (ValueError, TypeError):
                    pass
                imported += 1
        except (ValueError, TypeError) as exc:
            logger.warning("Invalid subscription entry %s=%s: %s", chat_id_str, patient_id_str, exc)

    logger.info("Imported %d subscriptions from JSON.", imported)
    return imported