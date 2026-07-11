from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsAuthenticatedAndRole
from .models import Appointment
from .serializers import AppointmentSerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related(
        "patient", "doctor", "department", "created_by"
    ).all()
    serializer_class = AppointmentSerializer
    allowed_roles = {"admin", "chief_doctor", "doctor", "registrar"}
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["patient", "doctor", "department", "status"]
    search_fields = ["patient__full_name", "reason", "doctor__last_name"]
    ordering_fields = ["scheduled_at", "created_at", "status"]
    ordering = ["-scheduled_at"]

    def get_permissions(self):
        return [IsAuthenticatedAndRole()]
