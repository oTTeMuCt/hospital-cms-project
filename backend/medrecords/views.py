from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from accounts.permissions import IsAdminRole, IsDoctor
from .models import MedicalRecord
from .serializers import MedicalRecordSerializer


class MedicalRecordViewSet(viewsets.ModelViewSet):
    queryset = MedicalRecord.objects.select_related("patient", "created_by", "appointment")
    serializer_class = MedicalRecordSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["patient", "appointment"]

    def get_permissions(self):
        return [IsAdminRole()] if self.action == "destroy" else [IsDoctor()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == "doctor":
            if self.action in ("update", "partial_update"):
                return queryset.filter(created_by=user)
            return queryset.filter(patient__in=MedicalRecordSerializer.care_patients(user))
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
