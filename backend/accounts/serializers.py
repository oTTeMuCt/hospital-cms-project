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
            "phone",
            "telegram_id",
            "pinfl",
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
            "phone",
            "telegram_id",
            "pinfl",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
