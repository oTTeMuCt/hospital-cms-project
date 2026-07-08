from rest_framework import viewsets

from accounts.permissions import IsRegistrar
from .models import Appointment
from .serializers import AppointmentSerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related(
        "patient", "doctor", "department", "created_by"
    ).all()
    serializer_class = AppointmentSerializer

    def get_permissions(self):
        return [IsRegistrar()]