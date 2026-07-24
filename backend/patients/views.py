import logging
import os
from django.db import transaction
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
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

logger = logging.getLogger("patients.views")


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
        if self.action == "me":
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

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Return the patient profile for the currently authenticated user."""
        try:
            patient = request.user.patient_profile
            serializer = self.get_serializer(patient)
            return Response(serializer.data)
        except Patient.DoesNotExist:
            return Response(
                {"detail": "No patient profile is linked to your account."},
                status=status.HTTP_404_NOT_FOUND,
            )


class BotLinkTelegramView(APIView):
    """
    Endpoint called by the Telegram Bot to link a Telegram chat_id to a Patient.
    Expects X-Bot-Key header for authentication.
    """

    permission_classes = [drf_permissions.AllowAny]

    def post(self, request):
        bot_api_key = os.getenv("BOT_API_KEY", "HCMS-Bot-2024-Secret")
        auth_header = request.META.get("HTTP_X_BOT_KEY", "")

        if not auth_header or auth_header != bot_api_key:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        patient_id = request.data.get("patient_id")
        telegram_id = request.data.get("telegram_id")

        if not patient_id or not telegram_id:
            return Response(
                {"error": "patient_id and telegram_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse patient_id — accept "P-000001" or "1" or even "000001"
        parsed_id = _parse_patient_id(patient_id)
        if parsed_id is None:
            return Response(
                {"error": f"Invalid patient_id format: {patient_id}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            patient = Patient.objects.get(pk=parsed_id)
        except Patient.DoesNotExist:
            return Response(
                {"error": f"Patient with id {patient_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        patient.telegram_id = str(telegram_id)
        patient.save(update_fields=["telegram_id"])
        logger.info(
            "Linked Telegram chat %s to patient %s (pk=%s)",
            telegram_id, patient_id, patient.pk,
        )

        return Response({"status": "ok", "patient_id": patient.pk})


def _parse_patient_id(raw: str) -> int | None:
    """Parse patient ID from formats like 'P-000001', '1', '000001'."""
    cleaned = raw.strip().upper()
    if cleaned.startswith("P-"):
        cleaned = cleaned[2:]
    elif cleaned.startswith("P"):
        cleaned = cleaned[1:]
    cleaned = cleaned.lstrip("0")
    if cleaned.isdigit():
        return int(cleaned)
    return None