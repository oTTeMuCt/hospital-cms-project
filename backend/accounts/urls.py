from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView

from .views import (
    AuthTokenObtainPairView,
    AuthTokenRefreshView,
    MeView,
    RegisterView,
    UserDetailView,
    UserListView,
)

urlpatterns = [
    path("auth/token/", AuthTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", AuthTokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/register/", RegisterView.as_view(), name="auth_register"),
    path("auth/me/", MeView.as_view(), name="auth_me"),
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user_detail"),
]
