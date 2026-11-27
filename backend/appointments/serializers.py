from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers

from .availability import DEFAULT_DURATION, occupied_bookings, work_interval
from .models import Appointment, AppointmentStatus, DoctorWorkHours

User = get_user_model()
STATUS_TRANSITIONS = {
    AppointmentStatus.PENDING: {AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED},
    AppointmentStatus.CONFIRMED: {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW},
    AppointmentStatus.CANCELLED: {AppointmentStatus.PENDING},
}


class AppointmentSerializer(serializers.ModelSerializer):
    doctor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role__in=["doctor", "chief_doctor"], is_active=True),
        allow_null=True, required=False,
    )
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
        read_only_fields = ["id", "created_at", "updated_at", "created_by"]

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None

    def get_doctor_name(self, obj):
        if obj.doctor:
            return obj.doctor.full_name_display if hasattr(obj.doctor, "full_name_display") else obj.doctor.get_full_name()
        return None

    def _prepare_booking(self, data, instance=None):
        doctor = data.get("doctor", getattr(instance, "doctor", None))
        start = data.get("scheduled_at", getattr(instance, "scheduled_at", None))
        end = data.get("end_time", getattr(instance, "end_time", None))
        status = data.get("status", getattr(instance, "status", AppointmentStatus.PENDING))

        if instance and "scheduled_at" in data and "end_time" not in data and end:
            end = start + (end - instance.scheduled_at)
        if end is None:
            end = start + DEFAULT_DURATION
        if end <= start:
            raise serializers.ValidationError({
                "end_time": "Время окончания должно быть позже времени начала."
            })
        data["end_time"] = end

        if not doctor or status == AppointmentStatus.CANCELLED:
            return

        # Lock the doctor before checking availability so concurrent API writes
        # for the same doctor cannot both reserve the interval in PostgreSQL.
        User.objects.select_for_update().get(pk=doctor.pk)
        overlapping = occupied_bookings(doctor, start, end)
        if instance:
            overlapping = overlapping.exclude(pk=instance.pk)
        conflict = overlapping.first()
        if conflict:
            conflict_end = conflict.end_time or conflict.scheduled_at + DEFAULT_DURATION
            raise serializers.ValidationError(
                f"Врач уже занят в это время. Конфликт с приёмом #{conflict.pk}: "
                f"{conflict.scheduled_at:%d.%m.%Y %H:%M} — {conflict_end:%H:%M}"
            )

    def _check_workday(self, data, instance=None):
        doctor = data.get("doctor", getattr(instance, "doctor", None))
        if doctor is None or data.get("status", getattr(instance, "status", None)) == AppointmentStatus.CANCELLED:
            return
        days = DoctorWorkHours.objects.filter(doctor=doctor)
        if not days.exists():
            return
        start = data.get("scheduled_at", getattr(instance, "scheduled_at", None))
        day = timezone.localdate(start, timezone.get_default_timezone())
        schedule = days.filter(weekday=day.weekday()).first()
        if schedule:
            opens, closes = work_interval(schedule, day)
            if opens <= start < data["end_time"] <= closes:
                return
        raise serializers.ValidationError({"scheduled_at": "Время вне рабочего графика врача."})

    def _check_role(self, data, instance=None):
        user = getattr(self.context.get("request"), "user", None)
        role = getattr(user, "role", None)
        if instance is None and data.get("status", AppointmentStatus.PENDING) != AppointmentStatus.PENDING:
            raise serializers.ValidationError({"status": "Новая запись должна ожидать подтверждения."})
        if role == "patient":
            if instance is None:
                if data["patient"].user_id != user.pk:
                    raise serializers.ValidationError({"patient": "Можно записать только себя."})
                if not data.get("doctor") or data["scheduled_at"] < timezone.now():
                    raise serializers.ValidationError({"scheduled_at": "Выберите врача и время в будущем."})
                if "notes" in data:
                    raise serializers.ValidationError({"notes": "Служебное примечание заполняет сотрудник."})
            elif set(data) != {"status"} or data["status"] != AppointmentStatus.CANCELLED:
                raise serializers.ValidationError("Пациент может только отменить свою запись.")
        if role == "doctor":
            if instance is None and data.get("doctor") != user:
                raise serializers.ValidationError({"doctor": "Врач может создать запись только на свой приём."})
            if instance is not None and set(data) - {"status", "notes"}:
                raise serializers.ValidationError("Врач может изменить статус и примечания своего приёма.")

        if instance and "status" in data and data["status"] != instance.status:
            if data["status"] not in STATUS_TRANSITIONS.get(instance.status, ()):
                raise serializers.ValidationError({"status": "Недопустимый переход статуса приёма."})
            if instance.status == AppointmentStatus.CANCELLED and "scheduled_at" not in data:
                raise serializers.ValidationError({"scheduled_at": "Укажите время для повторной записи."})

    @transaction.atomic
    def create(self, validated_data):
        self._check_role(validated_data)
        self._prepare_booking(validated_data)
        self._check_workday(validated_data)
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        current = get_object_or_404(Appointment.objects.select_for_update(), pk=instance.pk)
        self._check_role(validated_data, current)
        if {"doctor", "scheduled_at", "end_time", "status"}.intersection(validated_data):
            changes_slot = {"doctor", "scheduled_at", "end_time"}.intersection(validated_data)
            reopened = current.status == AppointmentStatus.CANCELLED and validated_data.get("status") == AppointmentStatus.PENDING
            self._prepare_booking(validated_data, current)
            if changes_slot or reopened:
                self._check_workday(validated_data, current)
        return super().update(current, validated_data)


class DoctorWorkHoursSerializer(serializers.ModelSerializer):
    doctor = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(
        role__in=["doctor", "chief_doctor"], is_active=True,
    ))

    class Meta:
        model = DoctorWorkHours
        fields = ["id", "doctor", "weekday", "starts_at", "ends_at"]

    def validate(self, attrs):
        if attrs.get("starts_at", getattr(self.instance, "starts_at", None)) >= attrs.get(
            "ends_at", getattr(self.instance, "ends_at", None),
        ):
            raise serializers.ValidationError({"ends_at": "Окончание должно быть после начала."})
        return attrs
