from django.db.models import Count
from django.db.models.functions import TruncDate
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsChiefDoctor
from patients.models import Patient
from lab.models import AnalysisOrder, AnalysisType
from appointments.models import Appointment
from hospitals.models import Department, Hospital


class ReportPeriodSerializer(serializers.Serializer):
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)

    def validate(self, data):
        if data.get("start") and data.get("end") and data["start"] > data["end"]:
            raise serializers.ValidationError({"end": "Конец периода раньше начала."})
        return data


def in_period(queryset, request, field):
    serializer = ReportPeriodSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    boundaries = (
        (f"{field}__date__gte", serializer.validated_data.get("start")),
        (f"{field}__date__lte", serializer.validated_data.get("end")),
    )
    return queryset.filter(**{key: value for key, value in boundaries if value is not None})


class PatientStatsView(APIView):
    """GET /api/stats/patients/ — количество пациентов по полу и группе крови."""
    permission_classes = [IsChiefDoctor]

    def get(self, request):
        total = Patient.objects.count()
        by_gender = (
            Patient.objects.values("gender")
            .annotate(count=Count("id"))
            .order_by("gender")
        )
        by_blood_group = (
            Patient.objects.values("blood_group")
            .annotate(count=Count("id"))
            .order_by("blood_group")
        )
        return Response({
            "total": total,
            "by_gender": list(by_gender),
            "by_blood_group": list(by_blood_group),
        })


class AnalysisStatsView(APIView):
    """GET /api/stats/analyses/ — количество анализов по статусу и типу."""
    permission_classes = [IsChiefDoctor]

    def get(self, request):
        orders = in_period(AnalysisOrder.objects.all(), request, "requested_at")
        total = orders.count()
        by_status = (
            orders.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        by_type = (
            orders.values("analysis_type__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        # Переименуем ключ для читаемости
        by_type_clean = [
            {"analysis_type": item["analysis_type__name"], "count": item["count"]}
            for item in by_type
        ]
        return Response({
            "total": total,
            "by_status": list(by_status),
            "by_type": by_type_clean,
        })


class DoctorStatsView(APIView):
    """GET /api/stats/doctors/ — количество приёмов на каждого врача."""
    permission_classes = [IsChiefDoctor]

    def get(self, request):
        doctor_counts = (
            in_period(Appointment.objects.all(), request, "scheduled_at").values(
                "doctor_id",
                "doctor__last_name",
                "doctor__first_name",
                "doctor__middle_name",
            )
            .annotate(appointment_count=Count("id"))
            .order_by("-appointment_count")
        )
        return Response(list(doctor_counts))


class HospitalStatsView(APIView):
    """GET /api/stats/hospitals/ — сводка по учреждениям."""
    permission_classes = [IsChiefDoctor]

    def get(self, request):
        total_hospitals = Hospital.objects.count()
        total_departments = Department.objects.count()
        hospitals = []
        for hospital in Hospital.objects.annotate(
            dept_count=Count("departments", distinct=True),
            staff_count=Count("staff", distinct=True),
        ):
            hospitals.append({
                "id": hospital.id,
                "name": hospital.name,
                "short_name": hospital.short_name,
                "department_count": hospital.dept_count,
                "staff_count": hospital.staff_count,
            })
        return Response({
            "total_hospitals": total_hospitals,
            "total_departments": total_departments,
            "hospitals": hospitals,
        })


class DailyStatsView(APIView):
    """GET /api/stats/daily/ — количество приёмов по дням."""
    permission_classes = [IsChiefDoctor]

    def get(self, request):
        daily = (
            in_period(Appointment.objects.all(), request, "scheduled_at").annotate(date=TruncDate("scheduled_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("-date")
        )
        return Response(list(daily))