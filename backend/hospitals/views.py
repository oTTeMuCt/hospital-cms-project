from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdminRole, IsAuthenticatedAndRole, IsChiefDoctor, IsRegistrar
from .models import Department, Hospital, Staff
from .serializers import DepartmentSerializer, HospitalSerializer, StaffAccountSerializer, StaffSerializer


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
        if self.action == "create_account":
            return [IsAdminRole()]
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedAndRole()]
        return [IsChiefDoctor()]


    @action(detail=False, methods=["post"], url_path="create-account", permission_classes=[IsAdminRole])
    def create_account(self, request):
        serializer = StaffAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = serializer.save()
        return Response(StaffSerializer(staff).data, status=status.HTTP_201_CREATED)
