from django.contrib.auth import get_user_model
from django.test import TestCase

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
