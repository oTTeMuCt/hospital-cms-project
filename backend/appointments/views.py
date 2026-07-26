from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsAuthenticatedAndRole, IsPatientOwnerOrStaff
from .models import Appointment
from .serializers import AppointmentSerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related(
        "patient", "doctor", "department", "created_by"
    ).all()
    serializer_class = AppointmentSerializer
    allowed_roles = {"admin", "chief_doctor", "doctor", "registrar", "patient"}
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["patient", "doctor", "department", "status"]
    search_fields = ["patient__full_name", "reason", "doctor__last_name"]
    ordering_fields = ["scheduled_at", "created_at", "status"]
    ordering = ["-scheduled_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsPatientOwnerOrStaff()]
        if self.action == "create":
            return [IsAuthenticatedAndRole()]
        if self.action in ("update", "partial_update"):
            return [IsAuthenticatedAndRole()]
        if self.action == "destroy":
            return [IsAuthenticatedAndRole()]
        return [IsPatientOwnerOrStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if user.role == "patient":
            # Patients see only their own appointments
            return qs.filter(patient__user=user)
        if user.role == "doctor":
            # Doctors see their own appointments
            return qs.filter(doctor=user)
        if user.role in ("admin", "chief_doctor", "registrar"):
            # Staff sees all appointments
            return qs
        return qs.none()
