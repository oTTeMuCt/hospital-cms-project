from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Patient
from .serializers import PatientSerializer


class PatientSerializerTests(TestCase):
    def test_national_id_and_serialization(self):
        User = get_user_model()
        user = User.objects.create_user(username="patient1", password="testpass", role="patient")
        # Signal auto-creates Patient profile; update it with test data
        patient = user.patient_profile
        patient.full_name = "Иванов Иван Иванович"
        patient.pinfl = "12345678901234"
        patient.phone = "+79990001122"
        patient.save()
        # Provide a request context with an authorized role that can see national_id
        class DummyUser:
            def __init__(self):
                self.role = "registrar"
                self.is_authenticated = True

        dummy_request = type("Req", (), {"user": DummyUser()})
        data = PatientSerializer(patient, context={"request": dummy_request}).data
        self.assertEqual(data["pinfl"], "12345678901234")
        self.assertEqual(data["phone"], "+79990001122")


class OptionalPatientFieldsTests(TestCase):
    def test_multiple_patients_can_use_blank_optional_fields(self):
        registrar = get_user_model().objects.create(username="registrar", role="registrar")
        client = APIClient()
        client.force_authenticate(registrar)
        payload = {"birth_date": "", "pinfl": "", "passport": "  "}
        for name in ("Patient 1", "Patient 2"):
            response = client.post("/api/patients/", {**payload, "full_name": name}, format="json")
            self.assertEqual(response.status_code, 201, response.data)
            patient = Patient.objects.get(pk=response.data["id"])
            self.assertIsNone(patient.birth_date)
            self.assertIsNone(patient.pinfl)
            self.assertIsNone(patient.passport)


class PatientOnboardingTests(TestCase):
    def test_patient_can_complete_existing_registration_profile(self):
        user = get_user_model().objects.create(username="new-patient", role="patient")
        client = APIClient()
        client.force_authenticate(user)
        response = client.patch("/api/patients/me/", {
            "full_name": "Complete Patient", "birth_date": "2001-02-03", "phone": "+998123456789",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], user.patient_profile.pk)
        self.assertEqual(response.data["full_name"], "Complete Patient")
        self.assertEqual(Patient.objects.filter(user=user).count(), 1)
