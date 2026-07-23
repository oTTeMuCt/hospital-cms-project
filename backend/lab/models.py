from django.conf import settings
from django.db import models

from patients.models import Patient


class AnalysisType(models.Model):
    name = models.CharField("Наименование анализа", max_length=255)
    code = models.CharField("Код анализа", max_length=64, unique=True)
    price = models.DecimalField("Стоимость", max_digits=12, decimal_places=2, default=0)
    currency = models.CharField("Валюта", max_length=8, default="UZS", help_text="ISO валюта, например UZS/USD/RUB")
    turnaround_days = models.PositiveSmallIntegerField("Срок выполнения (дней)", default=1)
    normal_range = models.CharField("Референсные значения", max_length=255, blank=True)
    description = models.TextField("Описание", blank=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Вид анализа"
        verbose_name_plural = "Виды анализов"
        ordering = ["name"]

    def __str__(self):
        return self.name


class AnalysisStatus(models.TextChoices):
    CREATED = "created", "Создан"
    ORDERED = "ordered", "Назначен"
    IN_PROGRESS = "in_progress", "В работе"
    COMPLETED = "completed", "Готов"
    VERIFIED = "verified", "Проверен врачом"
    SENT = "sent", "Отправлен пациенту"


ALLOWED_TRANSITIONS = {
    AnalysisStatus.CREATED: {AnalysisStatus.ORDERED},
    AnalysisStatus.ORDERED: {AnalysisStatus.IN_PROGRESS, AnalysisStatus.CREATED},
    AnalysisStatus.IN_PROGRESS: {AnalysisStatus.COMPLETED, AnalysisStatus.ORDERED},
    AnalysisStatus.COMPLETED: {AnalysisStatus.VERIFIED, AnalysisStatus.IN_PROGRESS},
    AnalysisStatus.VERIFIED: {AnalysisStatus.SENT, AnalysisStatus.COMPLETED},
    AnalysisStatus.SENT: set(),  # конечный статус
}


class AnalysisField(models.Model):
    """Predefined structured field for lab test results."""
    class FieldType(models.TextChoices):
        CHOICE = "choice", "Выбор из списка"
        NUMERIC = "numeric", "Числовой"
        TEXT = "text", "Текст"

    analysis_type = models.ForeignKey(
        AnalysisType,
        verbose_name="Вид анализа",
        on_delete=models.CASCADE,
        related_name="fields",
    )
    field_type = models.CharField(
        "Тип поля",
        max_length=16,
        choices=FieldType.choices,
    )
    field_name = models.CharField("Название поля", max_length=255)
    field_key = models.SlugField("Ключ поля (машинное имя)", max_length=64)
    options = models.JSONField(
        "Варианты выбора",
        null=True, blank=True,
        help_text='Список вариантов для choice-типа, напр. ["O (I) Rh+", "A (II) Rh-"]',
    )
    unit = models.CharField("Единица измерения", max_length=64, blank=True)
    reference_range_min = models.FloatField("Мин. референс", null=True, blank=True)
    reference_range_max = models.FloatField("Макс. референс", null=True, blank=True)
    reference_range_text = models.CharField("Референсные значения (текстом)", max_length=255, blank=True)
    is_required = models.BooleanField("Обязательное", default=True)
    sort_order = models.PositiveSmallIntegerField("Порядок сортировки", default=0)

    class Meta:
        verbose_name = "Поле результата анализа"
        verbose_name_plural = "Поля результатов анализов"
        ordering = ["analysis_type", "sort_order"]
        unique_together = (("analysis_type", "field_key"),)

    def __str__(self):
        return f"{self.analysis_type.name} — {self.field_name}"


class Interpretations(models.TextChoices):
    NORMAL = "normal", "Норма"
    HIGH = "high", "Повышен"
    LOW = "low", "Понижен"


class AnalysisResultValue(models.Model):
    """Stores a single field value for a lab analysis order."""
    analysis_order = models.ForeignKey(
        "AnalysisOrder",
        verbose_name="Заказ анализа",
        on_delete=models.CASCADE,
        related_name="result_values",
    )
    field = models.ForeignKey(
        AnalysisField,
        verbose_name="Поле",
        on_delete=models.CASCADE,
        related_name="result_values",
    )
    value = models.TextField("Значение", blank=True)
    interpretation = models.CharField(
        "Интерпретация",
        max_length=16,
        choices=Interpretations.choices,
        blank=True,
    )

    class Meta:
        verbose_name = "Значение результата"
        verbose_name_plural = "Значения результатов"
        unique_together = (("analysis_order", "field"),)

    def __str__(self):
        return f"{self.field.field_name}: {self.value[:50]}"


class AnalysisOrder(models.Model):
    patient = models.ForeignKey(
        Patient,
        verbose_name="Пациент",
        on_delete=models.CASCADE,
        related_name="analysis_orders",
    )
    orderer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Назначивший врач",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordered_analyses",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Лаборант (назначен)",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_analyses",
    )
    analysis_type = models.ForeignKey(
        AnalysisType,
        verbose_name="Вид анализа",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(
        "Статус",
        max_length=32,
        choices=AnalysisStatus.choices,
        default=AnalysisStatus.CREATED,
    )
    requested_at = models.DateTimeField("Дата назначения", auto_now_add=True)
    completed_at = models.DateTimeField("Дата завершения", null=True, blank=True)
    result = models.TextField("Результат", blank=True)
    result_data = models.JSONField("Данные результата", null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Проверил",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_analyses",
    )
    notes = models.TextField("Примечания", blank=True)

    class Meta:
        verbose_name = "Назначенный анализ"
        verbose_name_plural = "Назначенные анализы"
        ordering = ["-requested_at"]
        indexes = [models.Index(fields=["status", "requested_at"])]

    def __str__(self):
        return f"{self.analysis_type.name} — {self.patient.full_name}"