from django.contrib import admin

from .models import Department, Hospital


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "phone", "chief_doctor")
    search_fields = ("name", "address")
    list_filter = ("chief_doctor",)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "hospital", "department_type", "manager")
    search_fields = ("name", "hospital__name")
    list_filter = ("hospital", "department_type")
