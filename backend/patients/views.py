from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import (
    IsAdminRole,
    IsAuthenticatedAndRole,
    IsPatientOwnerOrStaff,
    IsRegistrar,
)
from rest_framework import permissions as drf_permissions
from .models import Patient
from .serializers import PatientSerializer


class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    allowed_roles = {"admin", "chief_doctor", "doctor", "lab_tech", "registrar"}
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "full_name", "phone", "email",
        "pinfl", "passport", "foreign_passport",
        "telegram_id",
    ]
    filterset_fields = ["gender", "blood_group"]
    ordering_fields = ["full_name", "created_at", "updated_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsPatientOwnerOrStaff()]
        if self.action == "create":
            # Регистратор, врач, главврач или лаборант
            return [IsAuthenticatedAndRole()]
        if self.action in ("update", "partial_update"):
            return [IsPatientOwnerOrStaff()]
        if self.action == "destroy":
            return [IsAdminRole()]
        return [IsPatientOwnerOrStaff()]

    def get_queryset(self):
        user = self.request.user
        qs = Patient.objects.all()
        if user.role == "patient":
            return qs.filter(user=user)
        if user.role in ("doctor", "chief_doctor", "lab_tech", "registrar", "admin"):
            return qs
        return qs.none()
