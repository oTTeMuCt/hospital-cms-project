from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "channel", "status", "created_at", "sent_at")
    search_fields = ("text", "subject")
    list_filter = ("channel", "status")
