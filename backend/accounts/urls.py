from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView

from .views import (
    AuthTokenObtainPairView,
    AuthTokenRefreshView,
    LogoutView,
    MeView,
    RegisterView,
    UserDetailView,
    UserListView,
)
from .password_reset import (
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
)

urlpatterns = [
    path("auth/token/", AuthTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", AuthTokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/logout/", LogoutView.as_view(), name="auth_logout"),
    path("auth/register/", RegisterView.as_view(), name="auth_register"),
    path("auth/me/", MeView.as_view(), name="auth_me"),
    path("auth/password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("auth/password-change/", PasswordChangeView.as_view(), name="password_change"),
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user_detail"),
]
