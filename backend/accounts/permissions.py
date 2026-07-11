from rest_framework import permissions

from .models import UserRole


class IsAdminRole(permissions.BasePermission):
    """Только администратор системы."""
    def has_permission(self, request, view):
        return _has_role(request, UserRole.ADMIN)


class IsChiefDoctor(permissions.BasePermission):
    """Главный врач и выше (админ)."""
    def has_permission(self, request, view):
        return _has_role(request, UserRole.CHIEF_DOCTOR) or _has_role(request, UserRole.ADMIN)


class IsDoctor(permissions.BasePermission):
    """Врач, главврач и админ."""
    def has_permission(self, request, view):
        return _has_any_role(request, {UserRole.DOCTOR, UserRole.CHIEF_DOCTOR, UserRole.ADMIN})


class IsLabTech(permissions.BasePermission):
    """Лаборант и выше."""
    def has_permission(self, request, view):
        return _has_any_role(request, {UserRole.LAB_TECH, UserRole.CHIEF_DOCTOR, UserRole.ADMIN})


class IsRegistrar(permissions.BasePermission):
    """Регистратор и выше."""
    def has_permission(self, request, view):
        return _has_any_role(request, {UserRole.REGISTRAR, UserRole.CHIEF_DOCTOR, UserRole.ADMIN})


class IsPatientOwnerOrStaff(permissions.BasePermission):
    """Пациент может видеть/менять только свои данные. Сотрудники — в рамках своей роли."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role != UserRole.PATIENT:
            return True  # staff — разрешено, фильтрация в queryset
        return True  # пациент — разрешено, но queryset будет отфильтрован

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role != UserRole.PATIENT:
            return True
        # Объект пациента (или объект с полем patient/user)
        patient_attr = getattr(obj, "patient", None)
        if patient_attr and hasattr(patient_attr, "user"):
            return patient_attr.user == request.user
        if hasattr(obj, "user"):
            return obj.user == request.user
        return False


class IsAuthenticatedAndRole(permissions.BasePermission):
    """Универсальный пермишн: view определяет allowed_roles."""
    def has_permission(self, request, view):
        allowed_roles = getattr(view, "allowed_roles", None)
        if not request.user or not request.user.is_authenticated:
            return False
        if allowed_roles is None:
            return True
        return request.user.role in allowed_roles


# ── helpers ──

def _has_role(request, role: str) -> bool:
    return bool(
        request.user
        and request.user.is_authenticated
        and request.user.role == role
    )


def _has_any_role(request, roles: set) -> bool:
    return bool(
        request.user
        and request.user.is_authenticated
        and request.user.role in roles
    )
