from django.contrib import admin

from .models import MedicalRecord


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ("patient", "primary_diagnosis", "updated_at")
    search_fields = ("patient__full_name", "primary_diagnosis", "allergies")
    list_filter = ("updated_at",)
