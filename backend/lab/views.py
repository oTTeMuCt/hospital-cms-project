import logging
import os

from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import (
    IsAdminRole,
    IsAuthenticatedAndRole,
    IsDoctor,
    IsLabTech,
)
from rest_framework import permissions as drf_permissions
from patients.models import Patient
from .models import AnalysisOrder, AnalysisType
from .serializers import AnalysisOrderSerializer, AnalysisTypeSerializer
from .bot_serializers import BotAnalysisResultSerializer

logger = logging.getLogger("lab.bot")


class AnalysisTypeViewSet(viewsets.ModelViewSet):
    queryset = AnalysisType.objects.all()
    serializer_class = AnalysisTypeSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdminRole()]


class AnalysisOrderViewSet(viewsets.ModelViewSet):
    queryset = AnalysisOrder.objects.select_related(
        "patient", "orderer", "assigned_to", "analysis_type", "verified_by"
    ).all()
    serializer_class = AnalysisOrderSerializer
    allowed_roles = {"admin", "doctor", "chief_doctor", "lab_tech", "registrar", "patient"}
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["patient", "status", "analysis_type"]
    search_fields = ["patient__full_name", "analysis_type__name", "result"]
    ordering_fields = ["requested_at", "status"]
    ordering = ["-requested_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            # Лаборант, врач, главврач, администратор — могут видеть
            return [IsAuthenticatedAndRole()]
        if self.action == "create":
            return [IsDoctor()]
        if self.action in ("update", "partial_update"):
            return [IsLabTech()]
        if self.action == "destroy":
            return [IsAdminRole()]
        return [IsLabTech()]

    def perform_create(self, serializer):
        serializer.save(orderer=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Пациенты видят только свои анализы
        if user.is_authenticated and user.role == "patient":
            return qs.filter(patient__user=user)
        return qs


class BotPatientAnalysesView(APIView):
    """
    Публичный эндпоинт для Telegram-бота.
    Принимает паспорт/ПИНФЛ и возвращает анализы пациента.
    Защита — заголовок X-Bot-Key.
    """
    permission_classes = []

    def get(self, request):
        bot_key = request.headers.get("X-Bot-Key")
        expected_key = os.getenv("BOT_API_KEY", "HCMS-Bot-2024-Secret")

        # Log incoming request details for diagnostics
        logger.info(
            "Bot request received: passport=%s, pinfl=%s, X-Bot-Key=%s, remote=%s",
            request.GET.get("passport", ""),
            request.GET.get("pinfl", ""),
            "***" if bot_key else "(none)",
            request.META.get("REMOTE_ADDR", "unknown"),
        )

        if not bot_key or bot_key != expected_key:
            logger.warning(
                "Bot auth failed: provided_key=%s, expected_key=%s",
                bot_key,
                expected_key,
            )
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        passport = request.GET.get("passport", "").strip()
        pinfl = request.GET.get("pinfl", "").strip()

        if not passport and not pinfl:
            logger.warning("Bot request missing passport and pinfl")
            return Response(
                {"error": "Укажите passport или pinfl"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if passport:
                patient = Patient.objects.get(passport__iexact=passport)
                logger.info("Patient found by passport: id=%s, name=%s", patient.id, patient.full_name)
            else:
                patient = Patient.objects.get(pinfl__iexact=pinfl)
                logger.info("Patient found by pinfl: id=%s, name=%s", patient.id, patient.full_name)
        except Patient.DoesNotExist:
            logger.warning("Patient not found: passport=%s, pinfl=%s", passport, pinfl)
            return Response({"error": "Пациент не найден"}, status=status.HTTP_404_NOT_FOUND)
        except Patient.MultipleObjectsReturned:
            logger.error(
                "Multiple patients found: passport=%s, pinfl=%s. Data integrity issue!",
                passport,
                pinfl,
            )
            return Response(
                {"error": "Найдено несколько пациентов. Обратитесь в регистратуру."},
                status=status.HTTP_409_CONFLICT,
            )

        analyses = AnalysisOrder.objects.filter(
            patient=patient
        ).select_related("analysis_type").order_by("-requested_at")

        serializer = BotAnalysisResultSerializer(analyses, many=True)
        analysis_count = len(serializer.data)
        logger.info(
            "Returning %d analyses for patient id=%s",
            analysis_count,
            patient.id,
        )

        return Response({
            "patient": {
                "id": patient.id,
                "full_name": patient.full_name,
                "birth_date": str(patient.birth_date) if patient.birth_date else None,
                "gender": patient.get_gender_display(),
            },
            "analyses": serializer.data,
        })
