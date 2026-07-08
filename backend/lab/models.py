from django.conf import settings
from django.db import models

from patients.models import Patient


class AnalysisType(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    turnaround_days = models.PositiveSmallIntegerField(default=1)
    normal_range = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Analysis Type"
        verbose_name_plural = "Analysis Types"
        ordering = ["name"]

    def __str__(self):
        return self.name


class AnalysisStatus(models.TextChoices):
    CREATED = "created", "Created"
    ORDERED = "ordered", "Ordered"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    VERIFIED = "verified", "Verified"
    SENT = "sent", "Sent"


class AnalysisOrder(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="analysis_orders")
    orderer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordered_analyses",
    )
    analysis_type = models.ForeignKey(AnalysisType, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=32, choices=AnalysisStatus.choices, default=AnalysisStatus.CREATED)
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result = models.TextField(blank=True)
    result_data = models.JSONField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_analyses",
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Analysis Order"
        verbose_name_plural = "Analysis Orders"
        ordering = ["-requested_at"]
        indexes = [models.Index(fields=["status", "requested_at"])]

    def __str__(self):
        return f"{self.analysis_type.name} for {self.patient.full_name}"
