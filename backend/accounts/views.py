import logging

from django.contrib.auth import get_user_model, authenticate
from rest_framework import generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .lockout import (
    apply_lockout,
    get_remaining_lockout_time,
    increment_failed_attempts,
    is_account_locked,
    reset_failed_attempts,
)
from .permissions import IsAdminRole
from .serializers import UserCreateSerializer, UserSerializer
from .throttling import LoginBurstThrottle, LoginRateThrottle

User = get_user_model()
logger = logging.getLogger("accounts.views")


class AuthTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/token/
    Authenticate and obtain JWT access/refresh tokens.
    Includes rate limiting, account lockout protection.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle, LoginBurstThrottle]

    def post(self, request, *args, **kwargs):
        # Check if username is provided
        username = request.data.get("username", "")
        password = request.data.get("password", "")

        if not username or not password:
            return Response(
                {"detail": "Укажите логин и пароль."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Find user for lockout check (before attempting password verification)
        user = None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            pass

        # Check account lockout
        if user and is_account_locked(user.pk):
            remaining = get_remaining_lockout_time(user.pk)
            logger.warning(
                "Blocked login attempt for locked account: username=%s, user_id=%s",
                username, user.pk,
            )
            return Response(
                {
                    "detail": f"Аккаунт временно заблокирован. Попробуйте через {remaining // 60} мин.",
                    "lockout_remaining_seconds": remaining,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Attempt authentication
        authenticated_user = authenticate(username=username, password=password)

        if authenticated_user is None:
            if user:
                attempts = increment_failed_attempts(user.pk)
                logger.warning(
                    "Failed login attempt for username=%s, user_id=%s, attempts=%d",
                    username, user.pk, attempts,
                )
                if attempts >= 5:
                    apply_lockout(user.pk)
                    return Response(
                        {
                            "detail": "Аккаунт временно заблокирован из-за множества неудачных попыток. Попробуйте через 15 мин.",
                            "lockout_remaining_seconds": 900,
                        },
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )
            return Response(
                {"detail": "Неверный логин или пароль."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Successful login - reset lockout counter
        reset_failed_attempts(user.pk)

        # Generate JWT tokens via parent class
        return super().post(request, *args, **kwargs)


class AuthTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklist the refresh token and clear client-side tokens.
    Requires authentication (access token in header).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token_value = request.data.get("refresh")

        if not refresh_token_value:
            return Response(
                {"detail": "Refresh token обязателен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token_value)
            token.blacklist()
            logger.info(
                "Token blacklisted for user_id=%s, username=%s",
                request.user.pk,
                request.user.username,
            )
            return Response(
                {"detail": "Вы успешно вышли из системы."},
                status=status.HTTP_200_OK,
            )
        except TokenError as exc:
            logger.warning(
                "Token blacklist failed for user_id=%s: %s",
                request.user.pk, exc,
            )
            return Response(
                {"detail": "Токен недействителен или уже отозван."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.error(
                "Unexpected error during logout for user_id=%s: %s",
                request.user.pk, exc,
            )
            return Response(
                {"detail": "Ошибка при выходе из системы."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.request.user.is_authenticated and self.request.user.role in {"admin", "registrar", "doctor", "chief_doctor"}:
            return [permissions.IsAuthenticated()]
        return [IsAdminRole()]


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]
