from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.serializers import SensitiveFieldsMixin
from .models import Department, DepartmentType, Hospital, Staff

User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    department_type_display = serializers.CharField(source="get_department_type_display", read_only=True)
    manager_name = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            "id", "hospital", "name", "department_type", "department_type_display",
            "manager", "manager_name", "description", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_manager_name(self, obj):
        if obj.manager:
            return obj.manager.full_name_display or obj.manager.get_full_name() or obj.manager.username
        return None


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

    def validate(self, attrs):
        department = attrs.get("department", getattr(self.instance, "department", None))
        hospital = attrs.get("hospital", getattr(self.instance, "hospital", None))
        if department and (not hospital or department.hospital_id != hospital.pk):
            raise serializers.ValidationError({"department": "Выберите отделение выбранной больницы."})
        return attrs

    def get_user_full_name(self, obj):
        return obj.user.full_name_display if hasattr(obj.user, "full_name_display") else obj.user.get_full_name()


class StaffAccountSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, validators=[User.username_validator])
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    role = serializers.ChoiceField(choices=["chief_doctor", "doctor", "lab_tech", "registrar"])
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    position = serializers.CharField(max_length=255)
    hospital = serializers.PrimaryKeyRelatedField(queryset=Hospital.objects.all(), required=False, allow_null=True)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), required=False, allow_null=True)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Такой логин уже существует.")
        return value

    def validate(self, attrs):
        department, hospital = attrs.get("department"), attrs.get("hospital")
        if department and (not hospital or department.hospital_id != hospital.pk):
            raise serializers.ValidationError({"department": "Выберите отделение выбранной больницы."})
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError

        user = User(username=attrs["username"], first_name=attrs["first_name"], last_name=attrs["last_name"])
        try:
            validate_password(attrs["password"], user)
        except ValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages}) from exc
        return attrs

    def create(self, validated_data):
        from django.db import IntegrityError, transaction

        account = {field: validated_data.pop(field) for field in ("username", "password", "role", "first_name", "last_name")}
        account["email"] = validated_data.pop("email", "")
        try:
            with transaction.atomic():
                user = User.objects.create_user(**account)
                return Staff.objects.create(user=user, **validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError({"username": "Такой логин уже существует."}) from exc
