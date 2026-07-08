from django.db import models

from patients.models import Patient


class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="medical_records")
    primary_diagnosis = models.CharField(max_length=255, blank=True)
    chronic_conditions = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    vaccinations = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Medical Record"
        verbose_name_plural = "Medical Records"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Medical record for {self.patient.full_name}"
