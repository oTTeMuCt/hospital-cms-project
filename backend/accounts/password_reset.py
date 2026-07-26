"""
Password reset and change functionality.

Provides secure token-based password reset flow and
authenticated password change endpoint.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
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

    def validate_email(self, value):
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Пользователь с таким email не найден.")
        return value


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
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Don't reveal whether email exists
            return Response(
                {"detail": "Если email зарегистрирован, инструкции отправлены."},
                status=status.HTTP_200_OK,
            )

        # Generate token
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        # Build reset link
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        reset_link = f"{frontend_url}/reset-password/{uidb64}/{token}/"

        # Send email
        try:
            subject = "Сброс пароля — Hospital CMS"
            message = render_to_string("accounts/password_reset_email.html", {
                "user": user,
                "reset_link": reset_link,
                "valid_hours": 24,
            })
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL or "noreply@hospitalcms.com",
                [email],
                fail_silently=False,
            )
            logger.info("Password reset email sent to %s (user_id=%s)", email, user.pk)
        except Exception as exc:
            logger.error("Failed to send password reset email to %s: %s", email, exc)
            return Response(
                {"detail": "Ошибка отправки email. Попробуйте позже."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

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

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uidb64 = serializer.validated_data["uidb64"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
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