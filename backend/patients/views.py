from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsPatientOwnerOrStaff, IsRegistrar
from .models import Patient
from .serializers import PatientSerializer


class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
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
            return [IsRegistrar()]
        if self.action == "create":
            return [IsRegistrar()]
        return [IsRegistrar()]

    def get_queryset(self):
        user = self.request.user
        qs = Patient.objects.all()
        if user.role == "patient":
            return qs.filter(user=user)
        return qs
