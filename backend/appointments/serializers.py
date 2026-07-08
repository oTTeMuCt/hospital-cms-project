from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Appointment

User = get_user_model()


class AppointmentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id", "patient", "doctor", "department", "reason",
            "scheduled_at", "end_time", "status", "status_display",
            "notes", "created_by", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]