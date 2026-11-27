from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, filters, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsAdminRole, IsAuthenticatedAndRole, IsChiefDoctor, IsPatientOwnerOrStaff
from .availability import DEFAULT_DURATION, occupied_bookings, work_interval
from .models import Appointment, DoctorWorkHours
from .serializers import AppointmentSerializer, DoctorWorkHoursSerializer

User = get_user_model()


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related(
        "patient", "doctor", "department", "created_by"
    ).all()
    serializer_class = AppointmentSerializer
    allowed_roles = {"admin", "chief_doctor", "doctor", "registrar", "patient"}
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {"patient": ["exact"], "doctor": ["exact"], "department": ["exact"], "status": ["exact"], "scheduled_at": ["date"]}
    search_fields = ["patient__full_name", "reason", "doctor__last_name"]
    ordering_fields = ["scheduled_at", "created_at", "status"]
    ordering = ["-scheduled_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsPatientOwnerOrStaff()]
        if self.action == "create":
            return [IsAuthenticatedAndRole()]
        if self.action in ("update", "partial_update"):
            return [IsAuthenticatedAndRole()]
        if self.action == "destroy":
            return [IsAdminRole()]
        return [IsPatientOwnerOrStaff()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if user.role == "patient":
            # Patients see only their own appointments
            return qs.filter(patient__user=user)
        if user.role == "doctor":
            # Doctors see their own appointments
            return qs.filter(doctor=user)
        if user.role in ("admin", "chief_doctor", "registrar"):
            # Staff sees all appointments
            return qs
        return qs.none()


class DoctorWorkHoursViewSet(viewsets.ModelViewSet):
    queryset = DoctorWorkHours.objects.all()
    serializer_class = DoctorWorkHoursSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["doctor"]
    permission_classes = [IsChiefDoctor]

    @transaction.atomic
    def perform_create(self, serializer):
        User.objects.select_for_update().get(pk=serializer.validated_data["doctor"].pk)
        serializer.save()

    @transaction.atomic
    def perform_update(self, serializer):
        doctor = serializer.validated_data.get("doctor", serializer.instance.doctor)
        if doctor.pk != serializer.instance.doctor_id:
            raise serializers.ValidationError({"doctor": "Создайте график для другого врача отдельно."})
        User.objects.select_for_update().get(pk=doctor.pk)
        serializer.save()

    @transaction.atomic
    def perform_destroy(self, instance):
        User.objects.select_for_update().get(pk=instance.doctor_id)
        instance.delete()


class SlotRequestSerializer(serializers.Serializer):
    doctor = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(
        role__in=["doctor", "chief_doctor"], is_active=True,
    ))
    date = serializers.DateField()


class BookingDoctorsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        doctors = User.objects.filter(role__in=["doctor", "chief_doctor"], is_active=True).order_by("last_name", "first_name")
        return Response([{"id": doctor.pk, "name": doctor.full_name_display} for doctor in doctors])


class AvailableSlotsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = SlotRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        doctor, day = (serializer.validated_data[key] for key in ("doctor", "date"))
        workday = DoctorWorkHours.objects.filter(doctor=doctor, weekday=day.weekday()).first()
        slots = []
        if workday:
            cursor, closes = work_interval(workday, day)
            bookings = list(occupied_bookings(doctor, cursor, closes))
            now = timezone.now()
            while cursor + DEFAULT_DURATION <= closes:
                end = cursor + DEFAULT_DURATION
                if cursor >= now and not any(
                    booking.scheduled_at < end and (booking.end_time or booking.scheduled_at + DEFAULT_DURATION) > cursor
                    for booking in bookings
                ):
                    slots.append({"start": cursor.isoformat(), "end": end.isoformat()})
                cursor = end
        return Response(slots)
