from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APIRequestFactory, force_authenticate

from .models import Patient
from .views import PatientViewSet
from hospitals.views import HospitalViewSet
from hospitals.models import Hospital


class PatientViewsetIntegrationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username="admin", password="pass", role="admin")
        self.registrar = User.objects.create_user(username="reg", password="pass", role="registrar")
        self.doctor = User.objects.create_user(username="doc", password="pass", role="doctor")

        # Signal auto-creates Patient profile; update it with test data
        self.patient_user = User.objects.create_user(username="patient1", password="testpass", role="patient")
        self.patient = self.patient_user.patient_profile
        self.patient.full_name = "Иванов И."
        self.patient.pinfl = "NID123456"
        self.patient.phone = "+79990001122"
        self.patient.save()

        self.factory = APIRequestFactory()

    def test_registrar_list_sees_national_id(self):
        request = self.factory.get("/api/patients/")
        force_authenticate(request, user=self.registrar)
        view = PatientViewSet.as_view({"get": "list"})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        results = response.data
        # should be a list
        self.assertTrue(isinstance(results, list) or "results" in response.data)
        # normalize list
        items = results if isinstance(results, list) else results.get("results", [])
        self.assertGreaterEqual(len(items), 1)
        self.assertIn("pinfl", items[0])

    def test_doctor_can_list_but_hides_national_id(self):
        request = self.factory.get("/api/patients/")
        force_authenticate(request, user=self.doctor)
        view = PatientViewSet.as_view({"get": "list"})
        response = view(request)
        # Doctors (staff) can list patients but pinfl should be hidden
        self.assertEqual(response.status_code, 200)
        items = response.data.get("results", []) if isinstance(response.data, dict) else response.data
        if items:
            self.assertNotIn("pinfl", items[0])

    def test_registrar_retrieve_sees_national_id(self):
        request = self.factory.get(f"/api/patients/{self.patient.id}/")
        force_authenticate(request, user=self.registrar)
        view = PatientViewSet.as_view({"get": "retrieve"})
        response = view(request, pk=self.patient.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn("pinfl", response.data)

    def test_doctor_retrieve_hides_national_id(self):
        request = self.factory.get(f"/api/patients/{self.patient.id}/")
        force_authenticate(request, user=self.doctor)
        view = PatientViewSet.as_view({"get": "retrieve"})
        response = view(request, pk=self.patient.id)
        # Doctors can retrieve patients but pinfl should be hidden via SensitiveFieldsMixin
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("pinfl", response.data)


class HospitalViewsetIntegrationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username="admin", password="pass", role="admin")
        self.registrar = User.objects.create_user(username="reg", password="pass", role="registrar")
        self.chief = User.objects.create_user(username="chief", password="pass", role="chief_doctor")

        self.hospital = Hospital.objects.create(name="Hosp", short_name="H1", timezone="Europe/Moscow", country_code="RU")
        self.factory = APIRequestFactory()

    def test_admin_retrieve_sees_timezone(self):
        request = self.factory.get(f"/api/hospitals/{self.hospital.id}/")
        force_authenticate(request, user=self.admin)
        view = HospitalViewSet.as_view({"get": "retrieve"})
        response = view(request, pk=self.hospital.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn("timezone", response.data)

    def test_registrar_retrieve_hides_timezone(self):
        request = self.factory.get(f"/api/hospitals/{self.hospital.id}/")
        force_authenticate(request, user=self.registrar)
        view = HospitalViewSet.as_view({"get": "retrieve"})
        response = view(request, pk=self.hospital.id)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("timezone", response.data)
