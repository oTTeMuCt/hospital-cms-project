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
    passport_series = models.CharField("Серия паспорта", max_length=4, blank=True, help_text="Серия паспорта РФ (4 цифры)")
    passport_number = models.CharField("Номер паспорта", max_length=6, blank=True, help_text="Номер паспорта РФ (6 цифр)")
    snils = models.CharField("СНИЛС", max_length=14, blank=True, help_text="Страховой номер индивидуального лицевого счёта")
    oms_policy = models.CharField("Полис ОМС", max_length=16, blank=True, help_text="Номер полиса обязательного медицинского страхования")
    national_id = models.CharField("Национальный идентификатор", max_length=64, blank=True, help_text="ПИНФЛ/ИНН/ИИН/другое")
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
            models.Index(fields=["snils"]),
            models.Index(fields=["oms_policy"]),
            models.Index(fields=["national_id"]),
        ]

    def __str__(self):
        return self.full_name
