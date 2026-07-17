from rest_framework import serializers
from django.db import models as db_models

from accounts.serializers import SensitiveFieldsMixin
from .models import Patient


class PatientSerializer(SensitiveFieldsMixin, serializers.ModelSerializer):
    gender_display = serializers.CharField(source="get_gender_display", read_only=True)
    blood_group_display = serializers.CharField(source="get_blood_group_display", read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id", "user", "full_name", "birth_date", "gender", "gender_display",
            "blood_group", "blood_group_display",
            "pinfl", "passport", "foreign_passport",
            "phone", "email", "telegram_id", "address", "emergency_contact",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_pinfl(self, value):
        if not value:
            return value
        # Check for existing pinfl (non-blank, non-null), excluding this instance on update
        qs = Patient.objects.filter(pinfl=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Пациент с таким ПИНФЛ уже зарегистрирован.")
        return value

    def validate_passport(self, value):
        if not value:
            return value
        # Check for existing passport (non-blank, non-null), excluding this instance on update
        qs = Patient.objects.filter(passport=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Пациент с таким паспортом уже зарегистрирован.")
        return value
