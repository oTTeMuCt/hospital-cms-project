from django.conf import settings
from django.db import models


class Gender(models.TextChoices):
    MALE = "male", "Мужской"
    FEMALE = "female", "Женский"


class BloodGroup(models.TextChoices):
    I_POS = "I+", "I+"
    I_NEG = "I-", "I-"
    II_POS = "II+", "II+"
    II_NEG = "II-", "II-"
    III_POS = "III+", "III+"
    III_NEG = "III-", "III-"
    IV_POS = "IV+", "IV+"
    IV_NEG = "IV-", "IV-"


class Patient(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="patient_profile",
        null=True,
        blank=True,
    )
    full_name = models.CharField("ФИО", max_length=255)
    birth_date = models.DateField("Дата рождения", null=True, blank=True)
    gender = models.CharField("Пол", max_length=16, choices=Gender.choices, blank=True)
    blood_group = models.CharField("Группа крови", max_length=8, choices=BloodGroup.choices, blank=True)
    pinfl = models.CharField(
        "ПИНФЛ",
        max_length=14,
        blank=True,
        unique=True,
        help_text="Персональный идентификационный номер физического лица (14 цифр)",
    )
    passport = models.CharField(
        "Паспорт",
        max_length=32,
        blank=True,
        help_text="Серия и номер паспорта гражданина Узбекистана (AB 1234567)",
    )
    foreign_passport = models.CharField(
        "Загранпаспорт / ID-карта иностранца",
        max_length=64,
        blank=True,
        help_text="Для иностранных граждан",
    )
    phone = models.CharField("Телефон", max_length=32, blank=True)
    email = models.EmailField("Email", blank=True)
    telegram_id = models.CharField("Telegram ID", max_length=64, blank=True)
    address = models.CharField("Адрес регистрации", max_length=512, blank=True)
    emergency_contact = models.CharField("Экстренный контакт", max_length=255, blank=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Пациент"
        verbose_name_plural = "Пациенты"
        ordering = ["full_name"]
        indexes = [
            models.Index(fields=["full_name"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["pinfl"]),
            models.Index(fields=["passport"]),
        ]

    def __str__(self):
        return self.full_name
