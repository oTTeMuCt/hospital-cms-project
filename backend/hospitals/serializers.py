from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.serializers import SensitiveFieldsMixin
from .models import Department, DepartmentType, Hospital, Staff

User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    department_type_display = serializers.CharField(source="get_department_type_display", read_only=True)

    class Meta:
        model = Department
        fields = [
            "id", "hospital", "name", "department_type", "department_type_display",
            "manager", "description", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DepartmentListSerializer(serializers.ModelSerializer):
    """Лёгкий сериализатор для вложенного списка."""
    class Meta:
        model = Department
        fields = ["id", "name", "department_type"]


class HospitalSerializer(SensitiveFieldsMixin, serializers.ModelSerializer):
    departments = DepartmentListSerializer(many=True, read_only=True)

    class Meta:
        model = Hospital
        fields = [
            "id", "name", "short_name", "address", "phone", "working_hours",
            "chief_doctor", "timezone", "country_code", "departments", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class StaffSerializer(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField()
    role = serializers.CharField(source="user.role", read_only=True)

    class Meta:
        model = Staff
        fields = [
            "id", "user", "user_full_name", "role",
            "hospital", "department", "position", "photo",
            "phone", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_user_full_name(self, obj):
        return obj.user.full_name_display if hasattr(obj.user, "full_name_display") else obj.user.get_full_name()
