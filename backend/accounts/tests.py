from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


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


class AccountsAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="admin",
            password="admin-password",
            email="admin@example.com",
            role="admin",
        )
        self.patient = get_user_model().objects.create_user(
            username="patient",
            password="patient-password",
            email="patient@example.com",
            role="patient",
        )

    def test_obtain_jwt_token(self):
        url = reverse("token_obtain_pair")
        response = self.client.post(url, {"username": "admin", "password": "admin-password"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_access_me_endpoint_with_token(self):
        token_url = reverse("token_obtain_pair")
        token_response = self.client.post(
            token_url,
            {"username": "patient", "password": "patient-password"},
            format="json",
        )
        access_token = token_response.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        me_url = reverse("auth_me")
        response = self.client.get(me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "patient")

    def test_admin_can_list_users(self):
        token_url = reverse("token_obtain_pair")
        token_response = self.client.post(
            token_url,
            {"username": "admin", "password": "admin-password"},
            format="json",
        )
        access_token = token_response.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(reverse("user_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_non_admin_cannot_list_users(self):
        token_url = reverse("token_obtain_pair")
        token_response = self.client.post(
            token_url,
            {"username": "patient", "password": "patient-password"},
            format="json",
        )
        access_token = token_response.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(reverse("user_list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
