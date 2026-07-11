from django.contrib import admin

from .models import File


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ("name", "file", "uploaded_by", "created_at")
    search_fields = ("name",)
    list_filter = ("created_at",)
