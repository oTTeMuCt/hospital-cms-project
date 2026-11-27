from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.timezone import now
from rest_framework.test import APIClient

from patients.models import Patient

from .models import Appointment


class AppointmentBookingTests(TestCase):
    def setUp(self):
        users = get_user_model().objects
        self.doctor = users.create(username="doctor", role="doctor")
        registrar = users.create(username="registrar", role="registrar")
        self.patient = Patient.objects.create(full_name="Test patient")
        self.client = APIClient()
        self.client.force_authenticate(registrar)
        self.start = now().replace(microsecond=0)
        self.payload = {
            "doctor": self.doctor.pk,
            "patient": self.patient.pk,
            "scheduled_at": self.start.isoformat(),
        }

    def test_missing_end_reserves_thirty_minutes_and_rejects_overlap(self):
        response = self.client.post("/api/appointments/", self.payload, format="json")
        self.assertEqual(response.status_code, 201)
        appointment = Appointment.objects.get(pk=response.data["id"])
        self.assertEqual(appointment.end_time, self.start + timedelta(minutes=30))

        response = self.client.post("/api/appointments/", self.payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_existing_record_without_end_blocks_overlap_but_allows_adjacent_slot(self):
        Appointment.objects.create(doctor=self.doctor, patient=self.patient, scheduled_at=self.start)

        overlap = {**self.payload, "scheduled_at": (self.start + timedelta(minutes=15)).isoformat()}
        response = self.client.post("/api/appointments/", overlap, format="json")
        self.assertEqual(response.status_code, 400)

        adjacent = {**self.payload, "scheduled_at": (self.start + timedelta(minutes=30)).isoformat()}
        response = self.client.post("/api/appointments/", adjacent, format="json")
        self.assertEqual(response.status_code, 201)

    def test_can_cancel_existing_conflict_and_reschedule_without_supplying_end(self):
        existing = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient, scheduled_at=self.start,
            end_time=self.start + timedelta(minutes=45),
        )
        Appointment.objects.create(doctor=self.doctor, patient=self.patient, scheduled_at=self.start)
        url = f"/api/appointments/{existing.pk}/"

        response = self.client.patch(url, {"status": "cancelled"}, format="json")
        self.assertEqual(response.status_code, 200)

        next_start = self.start + timedelta(hours=1)
        response = self.client.patch(
            url, {"status": "pending", "scheduled_at": next_start.isoformat()}, format="json",
        )
        self.assertEqual(response.status_code, 200)
        existing.refresh_from_db()
        self.assertEqual(existing.end_time, next_start + timedelta(minutes=45))


class PatientAppointmentPolicyTests(TestCase):
    def test_patient_can_book_and_cancel_own_pending_slot(self):
        users = get_user_model().objects
        patient_user = users.create(username="patient", role="patient")
        physician = users.create(username="physician", role="doctor")
        client = APIClient()
        client.force_authenticate(patient_user)
        booking = client.post("/api/appointments/", {
            "patient": patient_user.patient_profile.pk, "doctor": physician.pk, "scheduled_at": (now() + timedelta(days=1)).isoformat(),
        }, format="json")
        self.assertEqual(booking.status_code, 201)
        self.assertEqual(booking.data["created_by"], patient_user.pk)
        url = f"/api/appointments/{booking.data['id']}/"
        self.assertEqual(client.patch(url, {"status": "confirmed"}, format="json").status_code, 400)
        self.assertEqual(client.patch(url, {"status": "cancelled"}, format="json").status_code, 200)
        self.assertEqual(client.delete(url).status_code, 403)
