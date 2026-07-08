from django.contrib import admin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "email", "telegram_id")
    search_fields = ("full_name", "phone", "passport_number", "pinfl")
    list_filter = ("created_at",)
