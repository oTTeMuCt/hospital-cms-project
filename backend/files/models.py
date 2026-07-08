from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


def upload_to(instance, filename):
    """Загрузка файлов в: files/<app_label>/<model_name>/<object_id>/<filename>"""
    ct = instance.content_type
    return f"files/{ct.app_label}/{ct.model}/{instance.object_id}/{filename}"


class File(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        verbose_name="Тип объекта",
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveBigIntegerField("ID объекта")
    content_object = GenericForeignKey("content_type", "object_id")
    name = models.CharField("Название файла", max_length=255)
    file = models.FileField("Файл", upload_to=upload_to, max_length=1024, null=True, blank=True)
    mime_type = models.CharField("MIME-тип", max_length=128, blank=True)
    size = models.PositiveBigIntegerField("Размер (байт)", null=True, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Загрузил",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_files",
    )
    created_at = models.DateTimeField("Дата загрузки", auto_now_add=True)

    class Meta:
        verbose_name = "Файл"
        verbose_name_plural = "Файлы"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
