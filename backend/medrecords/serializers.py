from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import MedicalRecord

User = get_user_model()


class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = [
            "id", "patient", "diagnoses", "complaints", "surgeries",
            "chronic_conditions", "allergies", "vaccinations", "medications",
            "notes", "created_by", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]