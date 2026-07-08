from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import UserRole

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "middle_name",
            "role",
            "is_staff",
            "is_superuser",
        ]
        read_only_fields = ["id", "is_staff", "is_superuser"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=UserRole.choices, default=UserRole.PATIENT)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "middle_name",
            "role",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


# Sensitive fields mixin for serializers
class SensitiveFieldsMixin:
    """Mixin to remove sensitive fields from serializer.fields based on request.user.role.

    Define SENSITIVE_FIELDS mapping: model_name -> field -> allowed_roles(set)
    """
    SENSITIVE_FIELDS = {
        "Patient": {
            "national_id": {UserRole.ADMIN, UserRole.CHIEF_DOCTOR, UserRole.REGISTRAR},
        },
        "Hospital": {
            "timezone": {UserRole.ADMIN, UserRole.CHIEF_DOCTOR},
            "country_code": {UserRole.ADMIN, UserRole.CHIEF_DOCTOR},
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request") if hasattr(self, "context") else None
        user = getattr(request, "user", None)
        model = getattr(self.Meta, "model", None)
        model_name = getattr(model, "__name__", None)
        if not model_name:
            return
        field_map = self.SENSITIVE_FIELDS.get(model_name, {})
        if not field_map:
            return
        user_role = getattr(user, "role", None)
        for field, allowed in field_map.items():
            if field in self.fields:
                if user is None or not getattr(user, "is_authenticated", False) or user_role not in allowed:
                    # remove sensitive field for this user
                    self.fields.pop(field, None)
