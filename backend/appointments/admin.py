from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "department", "scheduled_at", "status")
    search_fields = ("patient__full_name", "doctor__username", "department__name")
    list_filter = ("status", "department")
