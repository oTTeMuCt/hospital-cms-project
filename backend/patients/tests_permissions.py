from django.contrib.auth import get_user_model
from django.test import TestCase

from patients.models import Patient
from patients.serializers import PatientSerializer
from hospitals.serializers import HospitalSerializer
from hospitals.models import Hospital


class DummyRequest:
    def __init__(self, user):
        self.user = user


class SensitiveFieldsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username="admin", password="pass", role="admin")
        self.chief = User.objects.create_user(username="chief", password="pass", role="chief_doctor")
        self.registrar = User.objects.create_user(username="reg", password="pass", role="registrar")
        self.doctor = User.objects.create_user(username="doc", password="pass", role="doctor")

        self.patient_user = User.objects.create_user(username="patient1", password="testpass", role="patient")
        self.patient = Patient.objects.create(user=self.patient_user, full_name="Иванов И.", pinfl="NID123456")

        self.hospital = Hospital.objects.create(name="Hosp", short_name="H1", timezone="Europe/Moscow", country_code="RU")

    def _wrap_user(self, user):
        # Return a lightweight object with role and is_authenticated attrs to avoid mutating Django User
        return type("U", (), {"role": user.role, "is_authenticated": True})()

    def test_registrar_sees_national_id(self):
        req = DummyRequest(self._wrap_user(self.registrar))
        data = PatientSerializer(self.patient, context={"request": req}).data
        self.assertIn("pinfl", data)
        self.assertEqual(data["pinfl"], "NID123456")

    def test_doctor_does_not_see_national_id(self):
        req = DummyRequest(self._wrap_user(self.doctor))
        data = PatientSerializer(self.patient, context={"request": req}).data
        self.assertNotIn("pinfl", data)

    def test_admin_sees_hospital_timezone(self):
        req = DummyRequest(self._wrap_user(self.admin))
        data = HospitalSerializer(self.hospital, context={"request": req}).data
        self.assertIn("timezone", data)
        self.assertEqual(data["timezone"], "Europe/Moscow")

    def test_registrar_does_not_see_hospital_timezone(self):
        req = DummyRequest(self._wrap_user(self.registrar))
        data = HospitalSerializer(self.hospital, context={"request": req}).data
        self.assertNotIn("timezone", data)
