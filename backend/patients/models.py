from django.conf import settings
from django.db import models


class Patient(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile",
        null=True,
        blank=True,
    )
    full_name = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    passport_number = models.CharField(max_length=64, blank=True)
    pinfl = models.CharField(max_length=14, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    telegram_id = models.CharField(max_length=64, blank=True)
    address = models.CharField(max_length=512, blank=True)
    insurance_number = models.CharField(max_length=64, blank=True)
    emergency_contact = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
        ordering = ["full_name"]
        indexes = [models.Index(fields=["full_name"]), models.Index(fields=["phone"])]

    def __str__(self):
        return self.full_name
