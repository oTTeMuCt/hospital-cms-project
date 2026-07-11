from django.contrib import admin

from .models import AnalysisOrder, AnalysisType


@admin.register(AnalysisType)
class AnalysisTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "price", "turnaround_days")
    search_fields = ("name", "code")


@admin.register(AnalysisOrder)
class AnalysisOrderAdmin(admin.ModelAdmin):
    list_display = ("patient", "analysis_type", "status", "requested_at")
    search_fields = ("patient__full_name", "analysis_type__name")
    list_filter = ("status",)
