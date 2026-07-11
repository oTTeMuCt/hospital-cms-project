from rest_framework import viewsets

from accounts.permissions import IsAdminRole, IsAuthenticatedAndRole, IsChiefDoctor, IsRegistrar
from .models import Department, Hospital, Staff
from .serializers import DepartmentSerializer, HospitalSerializer, StaffSerializer


class HospitalViewSet(viewsets.ModelViewSet):
    queryset = Hospital.objects.prefetch_related("departments").all()
    serializer_class = HospitalSerializer
    allowed_roles = {"admin", "chief_doctor", "doctor", "lab_tech", "registrar"}

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedAndRole()]
        return [IsAdminRole()]


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.select_related("hospital").all()
    serializer_class = DepartmentSerializer
    allowed_roles = {"admin", "chief_doctor", "doctor", "lab_tech", "registrar"}

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedAndRole()]
        return [IsChiefDoctor()]


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.select_related("user", "hospital", "department").all()
    serializer_class = StaffSerializer
    allowed_roles = {"admin", "chief_doctor", "doctor", "lab_tech", "registrar"}

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedAndRole()]
        return [IsChiefDoctor()]
