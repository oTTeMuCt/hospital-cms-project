from rest_framework import viewsets

from accounts.permissions import IsAdminRole, IsChiefDoctor, IsRegistrar
from .models import Department, Hospital, Staff
from .serializers import DepartmentSerializer, HospitalSerializer, StaffSerializer


class HospitalViewSet(viewsets.ModelViewSet):
    queryset = Hospital.objects.prefetch_related("departments").all()
    serializer_class = HospitalSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsRegistrar()]
        return [IsAdminRole()]


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.select_related("hospital").all()
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsRegistrar()]
        return [IsChiefDoctor()]


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.select_related("user", "hospital", "department").all()
    serializer_class = StaffSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsRegistrar()]
        return [IsChiefDoctor()]
