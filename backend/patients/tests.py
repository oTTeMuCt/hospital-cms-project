from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Patient
from .serializers import PatientSerializer


class PatientSerializerTests(TestCase):
    def test_national_id_and_serialization(self):
        User = get_user_model()
        user = User.objects.create_user(username="patient1", password="testpass", role="patient")
        patient = Patient.objects.create(
            user=user,
            full_name="Иванов Иван Иванович",
            national_id="12345678901234",
            phone="+79990001122",
        )
        data = PatientSerializer(patient).data
        self.assertEqual(data["national_id"], "12345678901234")
        self.assertEqual(data["phone"], "+79990001122")
