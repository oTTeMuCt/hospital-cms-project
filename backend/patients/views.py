from secrets import token_urlsafe

from django.core import signing
from django.db import transaction
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from notifications.subscription_models import Subscription

from accounts.permissions import (
    IsAdminRole,
    IsAuthenticatedAndRole,
    IsPatientOwnerOrStaff,
)
from rest_framework import permissions as drf_permissions
from .models import Patient
from .telegram import TELEGRAM_LINK_SALT
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
            return [IsAuthenticatedAndRole()]
        if self.action in ("update", "partial_update"):
            return [IsPatientOwnerOrStaff()]
        if self.action == "destroy":
            return [IsAdminRole()]
        if self.action in ("me", "telegram_link"):
            return [drf_permissions.IsAuthenticated()]
        return [IsPatientOwnerOrStaff()]

    def get_queryset(self):
        user = self.request.user
        qs = Patient.objects.all()
        if self.action in ("create", "update", "partial_update", "destroy"):
            qs = Patient.objects.select_for_update()
        if user.role == "patient":
            return qs.filter(user=user)
        if user.role in ("doctor", "chief_doctor", "lab_tech", "registrar", "admin"):
            return qs
        return qs.none()

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get", "patch"])
    @transaction.atomic
    def me(self, request):
        profiles = self.get_queryset().filter(user=request.user)
        if request.method == "PATCH":
            profiles = profiles.select_for_update()
        patient = profiles.first()
        if patient is None:
            return Response({"detail": "Профиль пациента не найден."}, status=status.HTTP_404_NOT_FOUND)
        if request.method == "PATCH":
            serializer = self.get_serializer(patient, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        else:
            serializer = self.get_serializer(patient)
        return Response({
            **serializer.data,
            "telegram_connected": Subscription.objects.filter(
                patient=patient, is_active=True, is_verified=True,
            ).exists(),
        })

    @action(detail=False, methods=["post"], url_path="telegram-link")
    @transaction.atomic
    def telegram_link(self, request):
        patient = Patient.objects.select_for_update().filter(user=request.user).first()
        if request.user.role != "patient" or patient is None:
            return Response({"detail": "Требуется профиль пациента."}, status=status.HTTP_403_FORBIDDEN)
        patient.telegram_link_nonce = token_urlsafe(18)
        patient.save(update_fields=["telegram_link_nonce"])
        code = signing.dumps(
            {"patient": patient.pk, "nonce": patient.telegram_link_nonce},
            salt=TELEGRAM_LINK_SALT,
        )
        return Response({"code": code}, headers={"Cache-Control": "private, no-store"})
