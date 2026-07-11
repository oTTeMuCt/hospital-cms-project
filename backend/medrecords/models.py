from django.conf import settings
from django.db import models

from patients.models import Patient


class MedicalRecord(models.Model):
    patient = models.ForeignKey(
        Patient,
        verbose_name="Пациент",
        on_delete=models.CASCADE,
        related_name="medical_records",
    )
    diagnoses = models.JSONField(
        "Диагнозы",
        default=list,
        blank=True,
        help_text='Список диагнозов, например [{"code": "I10", "name": "Эссенциальная гипертензия", "date": "2025-01-01"}]',
    )
    complaints = models.TextField("Жалобы", blank=True)
    surgeries = models.JSONField(
        "Операции",
        default=list,
        blank=True,
        help_text='Список операций, например [{"name": "Аппендэктомия", "date": "2024-06-15", "hospital": "ГКБ №1"}]',
    )
    chronic_conditions = models.TextField("Хронические заболевания", blank=True)
    allergies = models.TextField("Аллергические реакции", blank=True)
    vaccinations = models.TextField("Вакцинации", blank=True)
    medications = models.TextField("Лекарственные назначения", blank=True)
    notes = models.TextField("Заметки врача", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Врач",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_medrecords",
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Медицинская карта"
        verbose_name_plural = "Медицинские карты"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Мед. карта: {self.patient.full_name} ({self.created_at:%d.%m.%Y})"
