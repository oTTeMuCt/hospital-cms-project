from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .permissions import IsAdminRole
from .serializers import UserCreateSerializer, UserSerializer


User = get_user_model()


class AuthTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]


class AuthTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


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
        # Администратор может видеть всех пользователей
        # Регистратор/врач могут искать пользователей для привязки
        if self.request.user.is_authenticated and self.request.user.role in {"admin", "registrar", "doctor", "chief_doctor"}:
            return [permissions.IsAuthenticated()]
        return [IsAdminRole()]


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]
