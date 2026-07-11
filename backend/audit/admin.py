from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "user", "succeeded", "created_at")
    search_fields = ("action", "user__username", "ip_address")
    list_filter = ("succeeded",)
