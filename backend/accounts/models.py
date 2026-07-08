from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    CHIEF_DOCTOR = "chief_doctor", "Chief Doctor"
    DOCTOR = "doctor", "Doctor"
    LAB_TECH = "lab_tech", "Lab Technician"
    REGISTRAR = "registrar", "Registrar"
    PATIENT = "patient", "Patient"


class User(AbstractUser):
    middle_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=32, choices=UserRole.choices, default=UserRole.PATIENT)
    phone = models.CharField(max_length=32, blank=True)
    telegram_id = models.CharField(max_length=64, blank=True, null=True)
    pinfl = models.CharField(max_length=14, blank=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        if self.get_full_name():
            return self.get_full_name()
        return self.username
