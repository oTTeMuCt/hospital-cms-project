from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "admin", "Администратор"
    CHIEF_DOCTOR = "chief_doctor", "Главный врач"
    DOCTOR = "doctor", "Врач"
    LAB_TECH = "lab_tech", "Лаборант"
    REGISTRAR = "registrar", "Регистратор"
    PATIENT = "patient", "Пациент"


class User(AbstractUser):
    middle_name = models.CharField("Отчество", max_length=150, blank=True)
    role = models.CharField("Роль", max_length=32, choices=UserRole.choices, default=UserRole.PATIENT)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        full = self.get_full_name()
        if full:
            return full
        return self.username

    @property
    def full_name_display(self):
        """ФИО в формате: Фамилия Имя Отчество."""
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(p for p in parts if p)
