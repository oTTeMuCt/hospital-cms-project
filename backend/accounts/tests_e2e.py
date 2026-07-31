"""
End-to-end style tests for authentication flows.
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


@patch("accounts.views.AuthTokenObtainPairView.throttle_classes", [])
class AuthE2ETests(APITestCase):
    """End-to-end authentication flow tests."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="e2euser",
            password="TestPass123!",
            email="e2e@example.com",
            role="admin",
        )

    def test_login_and_access_protected_endpoint(self):
        resp = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "e2euser", "password": "TestPass123!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}"
        )
        me_resp = self.client.get(reverse("auth_me"))
        self.assertEqual(me_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(me_resp.data["username"], "e2euser")

    def test_logout_blacklists_refresh_token(self):
        resp = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "e2euser", "password": "TestPass123!"},
            format="json",
        )
        refresh = resp.data["refresh"]
        access = resp.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout_resp = self.client.post(
            reverse("auth_logout"),
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(logout_resp.status_code, status.HTTP_200_OK)

        refresh_resp = self.client.post(
            reverse("token_refresh"),
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(refresh_resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_password_change_flow(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            reverse("password_change"),
            {"old_password": "TestPass123!", "new_password": "NewPass456!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.client.logout()
        login_resp = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "e2euser", "password": "NewPass456!"},
            format="json",
        )
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)

    def test_registration_creates_patient_profile(self):
        resp = self.client.post(
            reverse("auth_register"),
            {
                "username": "newpatient",
                "email": "patient@example.com",
                "password": "PatientPass123!",
                "first_name": "Test",
                "last_name": "Patient",
                "role": "patient",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="newpatient")
        self.assertEqual(user.role, "patient")
        self.assertTrue(hasattr(user, "patient_profile"))
        self.assertIsNotNone(user.patient_profile)