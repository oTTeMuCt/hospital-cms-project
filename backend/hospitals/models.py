from django.conf import settings
from django.db import models


class DepartmentType(models.TextChoices):
    THERAPY = "therapy", "Терапия"
    SURGERY = "surgery", "Хирургия"
    CARDIOLOGY = "cardiology", "Кардиология"
    NEUROLOGY = "neurology", "Неврология"
    LABORATORY = "laboratory", "Лаборатория"
    XRAY = "xray", "Рентген"
    ULTRASOUND = "ultrasound", "УЗИ"
    RECEPTION = "reception", "Приёмное отделение"
    OTHER = "other", "Другое"


class Hospital(models.Model):
    name = models.CharField("Название", max_length=255)
    address = models.CharField("Адрес", max_length=512, blank=True)
    phone = models.CharField("Телефон", max_length=32, blank=True)
    working_hours = models.CharField("Режим работы", max_length=128, blank=True)
    chief_doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Главный врач",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chief_hospitals",
    )
    short_name = models.CharField("Краткое название", max_length=128, blank=True)
    timezone = models.CharField("Часовой пояс", max_length=64, blank=True, help_text="IANA timezone, например Europe/Moscow")
    country_code = models.CharField("Код страны", max_length=8, blank=True, help_text="ISO страны, например RU, KZ, UZ")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Медицинское учреждение"
        verbose_name_plural = "Медицинские учреждения"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(models.Model):
    hospital = models.ForeignKey(
        Hospital,
        verbose_name="Учреждение",
        on_delete=models.CASCADE,
        related_name="departments",
    )
    name = models.CharField("Название отделения", max_length=255)
    department_type = models.CharField(
        "Тип отделения",
        max_length=32,
        choices=DepartmentType.choices,
        default=DepartmentType.OTHER,
        blank=True,
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Заведующий отделением",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments",
    )
    description = models.TextField("Описание", blank=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Отделение"
        verbose_name_plural = "Отделения"
        unique_together = (("hospital", "name"),)
        ordering = ["hospital", "name"]

    def __str__(self):
        return f"{self.name} — {self.hospital.name}"


class Staff(models.Model):
    """Карточка сотрудника (ТЗ, Модуль 3)."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )
    hospital = models.ForeignKey(
        Hospital,
        verbose_name="Медицинское учреждение",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff",
    )
    department = models.ForeignKey(
        Department,
        verbose_name="Отделение",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff",
    )
    position = models.CharField("Должность", max_length=255)
    photo = models.ImageField("Фотография", upload_to="staff_photos/", null=True, blank=True)
    phone = models.CharField("Телефон", max_length=32, blank=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.position}"
