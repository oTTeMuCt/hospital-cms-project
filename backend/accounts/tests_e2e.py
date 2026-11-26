from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient


@override_settings(FRONTEND_URL="https://frontend.example.invalid/", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetTests(TestCase):
    def test_email_link_changes_password_and_cannot_be_reused(self):
        user = get_user_model().objects.create_user(
            username="patient", email="patient@example.invalid", password="old-test-password",
        )
        client = APIClient()
        request_url = "/api/auth/password-reset/"
        response = client.post(request_url, {"email": user.email}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        link = mail.outbox[0].body.split()[-1]
        u = urlsplit(link)
        self.assertEqual(u.path, "/reset-password/")
        uid, token = u.fragment.split("/")
        self.assertIn(link, mail.outbox[0].alternatives[0][0])

        confirm_url = "/api/auth/password-reset/confirm/"
        payload = {"uidb64": uid, "token": token, "new_password": "new-test-password"}
        response = client.post(confirm_url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password(payload["new_password"]))
        self.assertEqual(client.post(confirm_url, payload, format="json").status_code, 400)

        unknown = client.post(request_url, {"email": "unknown@example.invalid"}, format="json")
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
