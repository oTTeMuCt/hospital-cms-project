from django.contrib.auth import get_user_model
from django.test import TestCase


class AccountsModelTests(TestCase):
    def test_create_user_with_role(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="doctor1",
            password="strong-password",
            email="doc@example.com",
            first_name="Ivan",
            last_name="Petrov",
            role="doctor",
            phone="+998900000000",
        )

        self.assertTrue(user.pk)
        self.assertEqual(user.role, "doctor")
        self.assertEqual(user.email, "doc@example.com")
        self.assertFalse(user.is_staff)
