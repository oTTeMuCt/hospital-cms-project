from django.conf import settings
from django.db import models

from hospitals.models import Department
from patients.models import Patient


class AppointmentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    NO_SHOW = "no_show", "No-show"


class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
    )
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointments")
    reason = models.CharField(max_length=512, blank=True)
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=32, choices=AppointmentStatus.choices, default=AppointmentStatus.PENDING)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_appointments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"
        ordering = ["-scheduled_at"]
        indexes = [models.Index(fields=["scheduled_at", "status"])]

    def __str__(self):
        return f"Appointment for {self.patient.full_name} at {self.scheduled_at:%Y-%m-%d %H:%M}"
