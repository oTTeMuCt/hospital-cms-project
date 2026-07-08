from rest_framework import serializers

from .models import BloodGroup, Gender, Patient


class PatientSerializer(serializers.ModelSerializer):
    gender_display = serializers.CharField(source="get_gender_display", read_only=True)
    blood_group_display = serializers.CharField(source="get_blood_group_display", read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id", "user", "full_name", "birth_date", "gender", "gender_display",
            "blood_group", "blood_group_display",
            "passport_series", "passport_number", "snils", "national_id", "oms_policy",
            "phone", "email", "telegram_id", "address", "emergency_contact",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
