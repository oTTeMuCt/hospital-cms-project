from django.conf import settings
from django.db import models

from hospitals.models import Department
from patients.models import Patient


class AppointmentStatus(models.TextChoices):
    PENDING = "pending", "Ожидает подтверждения"
    CONFIRMED = "confirmed", "Подтверждена"
    COMPLETED = "completed", "Завершена"
    CANCELLED = "cancelled", "Отменена"
    NO_SHOW = "no_show", "Неявка"


class Appointment(models.Model):
    patient = models.ForeignKey(
        Patient,
        verbose_name="Пациент",
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Врач",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
    )
    department = models.ForeignKey(
        Department,
        verbose_name="Отделение",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
    )
    reason = models.CharField("Причина обращения", max_length=512, blank=True)
    scheduled_at = models.DateTimeField("Дата и время приёма")
    end_time = models.DateTimeField("Окончание приёма", null=True, blank=True, help_text="Если известно заранее")
    status = models.CharField(
        "Статус",
        max_length=32,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.PENDING,
    )
    notes = models.TextField("Заметки", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Кем создана",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_appointments",
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Запись на приём"
        verbose_name_plural = "Записи на приём"
        ordering = ["-scheduled_at"]
        indexes = [models.Index(fields=["scheduled_at", "status"])]

    def __str__(self):
        return f"Приём: {self.patient.full_name} — {self.scheduled_at:%d.%m.%Y %H:%M}"
