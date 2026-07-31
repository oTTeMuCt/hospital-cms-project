import logging
import os

from django.db.models import Q
from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import (
    IsAdminRole,
    IsAuthenticatedAndRole,
    IsDoctor,
    IsDoctorOrLabTech,
    IsLabTech,
)
from rest_framework import permissions as drf_permissions
from patients.models import Patient
from .models import AnalysisOrder, AnalysisStatus, AnalysisType
from .serializers import AnalysisOrderSerializer, AnalysisTypeDetailSerializer, AnalysisTypeSerializer
from .bot_serializers import BotAnalysisResultSerializer

logger = logging.getLogger("lab.bot")
debug_logger = logging.getLogger("lab.views")
debug_logger.setLevel(logging.DEBUG)
debug_logger.addHandler(logging.StreamHandler())
debug_logger.propagate = False


class AnalysisTypeViewSet(viewsets.ModelViewSet):
    queryset = AnalysisType.objects.all()
    serializer_class = AnalysisTypeSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AnalysisTypeDetailSerializer
        return AnalysisTypeSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdminRole()]


class AnalysisOrderViewSet(viewsets.ModelViewSet):
    queryset = AnalysisOrder.objects.select_related(
        "patient", "orderer", "assigned_to", "analysis_type", "verified_by"
    ).prefetch_related(
        "analysis_type__fields"
    ).all()
    serializer_class = AnalysisOrderSerializer
    allowed_roles = {"admin", "doctor", "chief_doctor", "lab_tech", "registrar", "patient"}
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["patient", "status", "analysis_type"]
    search_fields = ["patient__full_name", "analysis_type__name", "result"]
    ordering_fields = ["requested_at", "status"]
    ordering = ["-requested_at"]

    def get_permissions(self):
        debug_logger.debug(
            "=== PERMISSION CHECK === action=%s, user=%s (id=%s), role=%s, authenticated=%s",
            self.action,
            getattr(self.request, "user", None),
            getattr(getattr(self.request, "user", None), "id", None),
            getattr(getattr(self.request, "user", None), "role", None),
            getattr(getattr(self.request, "user", None), "is_authenticated", None),
        )
        if self.action in ("list", "retrieve"):
            # Лаборант, врач, главврач, администратор — могут видеть
            perm = IsAuthenticatedAndRole()
            result = perm.has_permission(self.request, self)
            debug_logger.debug("IsAuthenticatedAndRole result: %s", result)
            return [perm]
        if self.action == "create":
            # Только врач может назначить анализ
            perm = IsDoctor()
            result = perm.has_permission(self.request, self)
            debug_logger.debug("IsDoctor result: %s", result)
            return [perm]
        if self.action in ("update", "partial_update"):
            # Врачи могут обновлять статус (назначить/проверить), лаборанты — вводить результаты
            return [IsDoctorOrLabTech()]
        if self.action == "destroy":
            return [IsAdminRole()]
        return [IsLabTech()]

    def perform_create(self, serializer):
        serializer.save(orderer=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        # Пациенты видят только свои анализы
        if user.role == "patient":
            return qs.filter(patient__user=user)
        # Doctors see their ordered analyses
        if user.role == "doctor":
            return qs.filter(orderer=user)
        # Lab techs see unassigned analyses (queue) + their own assigned analyses
        if user.role == "lab_tech":
            return qs.filter(Q(assigned_to__isnull=True) | Q(assigned_to=user))
        # Admin/chief_doctor/registrar see all
        if user.role in ("admin", "chief_doctor", "registrar"):
            return qs
        return qs.none()

    def perform_update(self, serializer):
        """
        Delegate workflow state machine to the serializer's update() method.
        
        The serializer handles:
        - Lab Tech auto-assignment when accepting an analysis
        - Auto-completion when Lab Tech saves results
        - Status transitions based on current DB state, user role, and data presence
        """
        serializer.save()


class BotPatientAnalysesView(APIView):
    """
    Публичный эндпоинт для Telegram-бота.
    Принимает паспорт/ПИНФЛ и возвращает анализы пациента.
    Защита — заголовок X-Bot-Key.
    """
    permission_classes = []

    def get(self, request):
        bot_key = request.headers.get("X-Bot-Key")
        expected_key = os.getenv("BOT_API_KEY")
        if not expected_key:
            logger.error("BOT_API_KEY not configured")
            return Response({"error": "Service configuration error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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