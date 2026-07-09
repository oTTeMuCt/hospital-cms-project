import os

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminRole, IsDoctor, IsLabTech
from patients.models import Patient
from .models import AnalysisOrder, AnalysisType
from .serializers import AnalysisOrderSerializer, AnalysisTypeSerializer
from .bot_serializers import BotAnalysisResultSerializer


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

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsLabTech()]
        if self.action == "create":
            return [IsDoctor()]
        if self.action in ("update", "partial_update"):
            return [IsLabTech()]
        if self.action == "destroy":
            return [IsAdminRole()]
        return [IsLabTech()]


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
        if not bot_key or bot_key != expected_key:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        passport = request.GET.get("passport", "").strip()
        pinfl = request.GET.get("pinfl", "").strip()

        if not passport and not pinfl:
            return Response(
                {"error": "Укажите passport или pinfl"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if passport:
                patient = Patient.objects.get(passport__iexact=passport)
            else:
                patient = Patient.objects.get(pinfl__iexact=pinfl)
        except Patient.DoesNotExist:
            return Response({"error": "Пациент не найден"}, status=status.HTTP_404_NOT_FOUND)

        analyses = AnalysisOrder.objects.filter(
            patient=patient
        ).select_related("analysis_type").order_by("-requested_at")

        serializer = BotAnalysisResultSerializer(analyses, many=True)

        return Response({
            "patient": {
                "id": patient.id,
                "full_name": patient.full_name,
                "birth_date": str(patient.birth_date) if patient.birth_date else None,
                "gender": patient.get_gender_display(),
            },
            "analyses": serializer.data,
        })
