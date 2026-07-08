from rest_framework import permissions

from .models import UserRole


class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.ADMIN
        )


class IsAuthenticatedAndRole(permissions.BasePermission):
    def has_permission(self, request, view):
        allowed_roles = getattr(view, "allowed_roles", None)
        if not request.user or not request.user.is_authenticated:
            return False
        if allowed_roles is None:
            return True
        return request.user.role in allowed_roles
