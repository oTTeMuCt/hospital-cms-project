"""
Password reset and change functionality.

Provides secure token-based password reset flow and
authenticated password change endpoint.
"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

User = get_user_model()
logger = logging.getLogger("accounts.password_reset")

# Token generator instance
token_generator = PasswordResetTokenGenerator()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8, max_length=128)

    def validate_new_password(self, value):
        # Basic password strength validation
        if len(value) < 8:
            raise serializers.ValidationError("Пароль должен содержать минимум 8 символов.")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(min_length=8, max_length=128)

    def validate_old_password(self, value):
        user = self.context.get("user")
        if user and not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль неверен.")
        return value

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Новый пароль должен содержать минимум 8 символов.")
        return value


class PasswordResetRequestView(APIView):
    """
    POST /api/auth/password-reset/
    Request a password reset email.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        frontend_url = settings.FRONTEND_URL.rstrip("/")
        valid_hours = settings.PASSWORD_RESET_TIMEOUT / 3600

        for user in PasswordResetForm().get_users(email):
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            reset_link = f"{frontend_url}/reset-password/#{uidb64}/{token}"
            try:
                message = render_to_string("accounts/password_reset_email.html", {
                    "user": user,
                    "reset_link": reset_link,
                    "valid_hours": f"{valid_hours:g}",
                })
                send_mail(
                    "Сброс пароля — Hospital CMS",
                    f"Ссылка для сброса пароля: {reset_link}",
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                    html_message=message,
                )
            except Exception as exc:
                logger.error("Could not send password reset email (%s)", type(exc).__name__)

        return Response(
            {"detail": "Если email зарегистрирован, инструкции отправлены."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """
    POST /api/auth/password-reset/confirm/
    Confirm password reset with token and set new password.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    @transaction.atomic
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uidb64 = serializer.validated_data["uidb64"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.select_for_update().get(pk=uid, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Недействительная ссылка для сброса пароля."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not token_generator.check_token(user, token):
            return Response(
                {"detail": "Ссылка для сброса пароля недействительна или истекла."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])
        logger.info("Password reset completed for user_id=%s", user.pk)

        return Response(
            {"detail": "Пароль успешно изменён."},
            status=status.HTTP_200_OK,
        )


class PasswordChangeView(APIView):
    """
    POST /api/auth/password-change/
    Change password for authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={"user": request.user},
        )
        serializer.is_valid(raise_exception=True)

        new_password = serializer.validated_data["new_password"]
        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
        logger.info("Password changed for user_id=%s", request.user.pk)

        return Response(
            {"detail": "Пароль успешно изменён."},
            status=status.HTTP_200_OK,
        )
