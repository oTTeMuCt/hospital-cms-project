from django.contrib import admin

from .models import MedicalRecord


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ("patient", "updated_at")
    search_fields = ("patient__full_name", "diagnoses", "allergies")
    list_filter = ("updated_at",)
