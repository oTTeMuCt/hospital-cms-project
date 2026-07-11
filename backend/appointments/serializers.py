from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers

from .models import Appointment, AppointmentStatus

User = get_user_model()


class AppointmentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            "id", "patient", "patient_name", "doctor", "doctor_name", "department", "reason",
            "scheduled_at", "end_time", "status", "status_display",
            "notes", "created_by", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None

    def get_doctor_name(self, obj):
        if obj.doctor:
            return obj.doctor.full_name_display if hasattr(obj.doctor, "full_name_display") else obj.doctor.get_full_name()
        return None

    def validate(self, data):
        doctor = data.get("doctor", getattr(self.instance, "doctor", None))
        scheduled_at = data.get("scheduled_at", getattr(self.instance, "scheduled_at", None))
        end_time = data.get("end_time", getattr(self.instance, "end_time", None))
        instance_pk = self.instance.pk if self.instance else None

        if doctor and scheduled_at:
            if end_time is None:
                end_time = scheduled_at + timedelta(minutes=30)

            if end_time <= scheduled_at:
                raise serializers.ValidationError({
                    "end_time": "Время окончания должно быть позже времени начала."
                })

            overlapping = Appointment.objects.filter(
                doctor=doctor,
                scheduled_at__lt=end_time,
                end_time__gt=scheduled_at,
            ).exclude(status=AppointmentStatus.CANCELLED)

            if instance_pk:
                overlapping = overlapping.exclude(pk=instance_pk)

            if overlapping.exists():
                conflict = overlapping.first()
                raise serializers.ValidationError(
                    f"Врач уже занят в это время. Конфликт с приёмом #{conflict.pk}: "
                    f"{conflict.scheduled_at:%d.%m.%Y %H:%M} — "
                    f"{conflict.end_time:%H:%M if conflict.end_time else '?'}"
                )

        return data
