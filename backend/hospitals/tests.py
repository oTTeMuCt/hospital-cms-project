from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Department, Hospital


class HospitalsModelTests(TestCase):
    def test_hospital_and_department_creation(self):
        User = get_user_model()
        chief = User.objects.create_user(username="chief", password="password", role="chief_doctor")
        hospital = Hospital.objects.create(
            name="Central Hospital",
            address="Tashkent, 1 Main St",
            phone="+998900000001",
            working_hours="08:00-18:00",
            chief_doctor=chief,
        )
        department = Department.objects.create(
            hospital=hospital,
            name="Cardiology",
            department_type="cardiology",
            manager=chief,
        )

        self.assertEqual(str(hospital), "Central Hospital")
        self.assertEqual(str(department), "Cardiology — Central Hospital")
        self.assertEqual(department.hospital, hospital)
        self.assertEqual(department.manager, chief)
