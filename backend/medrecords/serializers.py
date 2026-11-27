from django.contrib.contenttypes.models import ContentType
from django.db.models import Exists, OuterRef
from appointments.models import Appointment, AppointmentStatus
from rest_framework import serializers

from patients.models import Patient
from .models import MedicalRecord


class MedicalRecordSerializer(serializers.ModelSerializer):
    attachment_content_type = serializers.SerializerMethodField()
    author_name = serializers.CharField(source="created_by.full_name_display", read_only=True, default="")

    class Meta:
        model = MedicalRecord
        fields = [
            "id", "patient", "appointment", "diagnoses", "complaints", "surgeries",
            "chronic_conditions", "allergies", "vaccinations", "medications",
            "notes", "created_by", "author_name", "created_at", "updated_at", "attachment_content_type",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_attachment_content_type(self, instance):
        return ContentType.objects.get_for_model(MedicalRecord).pk

    @staticmethod
    def care_patients(user):
        visits = Appointment.objects.filter(
            patient_id=OuterRef("pk"), doctor=user,
            status__in=[AppointmentStatus.CONFIRMED, AppointmentStatus.COMPLETED],
        )
        own_records = MedicalRecord.objects.filter(patient_id=OuterRef("pk"), created_by=user)
        return Patient.objects.filter(Exists(visits) | Exists(own_records))

    def validate(self, attrs):
        user = self.context["request"].user
        patient = attrs.get("patient", getattr(self.instance, "patient", None))
        visit = attrs.get("appointment", getattr(self.instance, "appointment", None))
        if self.instance and patient != self.instance.patient:
            raise serializers.ValidationError({"patient": "Нельзя перенести запись в другую медкарту."})
        if user.role == "doctor" and not self.care_patients(user).filter(pk=patient.pk).exists():
            raise serializers.ValidationError({"patient": "Пациент не связан с вашими приёмами."})
        for field in ("diagnoses", "surgeries"):
            if field in attrs and (
                not isinstance(attrs[field], list)
                or any(not isinstance(item, (dict, str)) for item in attrs[field])
            ):
                raise serializers.ValidationError({field: "Введите список записей."})
        if visit and (visit.patient_id != patient.pk or (user.role == "doctor" and visit.doctor_id != user.pk)):
            raise serializers.ValidationError({"appointment": "Выберите подходящий приём этого пациента."})
        return attrs
