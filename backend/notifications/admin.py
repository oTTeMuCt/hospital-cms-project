from django.contrib import admin

from .models import Notification
from .subscription_models import Subscription


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("subject", "channel", "recipient_content_type", "status", "created_at")
    list_filter = ("channel", "status")
    search_fields = ("subject", "text")
    ordering = ("-created_at",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("chat_id", "patient", "patient_id_str", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("chat_id", "patient__full_name", "patient_id_str")
    ordering = ("-created_at",)
    actions = ["unlock_all"]

    def unlock_all(self, request, queryset):
        """Reactivate all selected subscriptions."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Активировано {updated} подписок.")
    unlock_all.short_description = "Активировать выбранные подписки"