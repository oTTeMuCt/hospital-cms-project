from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from kombu.exceptions import OperationalError
from rest_framework.test import APIClient

from patients.models import Patient

from .models import Notification, NotificationStatus
from .tasks import send_notification


class NotificationDeliveryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.registrar = users.create(username="registrar", role="registrar")
        cls.patient_user = users.create(username="patient", role="patient")
        cls.recipient = Patient.objects.create(email="recipient@example.invalid")
        cls.payload = {
            "recipient_content_type": ContentType.objects.get_for_model(Patient).pk,
            "recipient_object_id": cls.recipient.pk,
            "channel": "email",
            "text": "Test notification",
        }

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.registrar)

    @patch("notifications.views.send_notification.delay")
    def test_creation_queues_after_commit(self, delay):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post("/api/notifications/", self.payload, format="json")
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.data["status"], NotificationStatus.PENDING)
            delay.assert_not_called()

        delay.assert_called_once_with(response.data["id"])

    @patch("notifications.views.send_notification.delay")
    def test_patient_cannot_queue_notifications(self, delay):
        self.client.force_authenticate(self.patient_user)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post("/api/notifications/", self.payload, format="json")

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Notification.objects.exists())
        delay.assert_not_called()

    @patch("notifications.views.send_notification.delay", side_effect=OperationalError)
    def test_queue_failure_marks_saved_notification_failed(self, delay):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post("/api/notifications/", self.payload, format="json")

        notification = Notification.objects.get(pk=response.data["id"])
        self.assertEqual(notification.status, NotificationStatus.FAILED)
        self.assertEqual(notification.error_message, "Notification queue is unavailable.")

    @patch("notifications.tasks.send_email_notification")
    def test_transient_failure_retries_and_delivers(self, send_email):
        notification = Notification.objects.create(recipient=self.recipient, channel="email", text="Test notification")
        send_email.side_effect = [RuntimeError("Provider detail"), None]

        result = send_notification.apply(args=[notification.pk]).get()

        notification.refresh_from_db()
        self.assertEqual(result["status"], "sent")
        self.assertEqual(notification.status, NotificationStatus.SENT)
        self.assertEqual(notification.error_message, "")
        self.assertEqual(send_email.call_count, 2)

        duplicate = send_notification.apply(args=[notification.pk]).get()
        self.assertEqual(duplicate["status"], "skipped")
        self.assertEqual(send_email.call_count, 2)

    @patch("notifications.tasks.send_email_notification", side_effect=RuntimeError("Provider detail"))
    def test_exhausted_retries_store_safe_failure(self, send_email):
        notification = Notification.objects.create(recipient=self.recipient, channel="email", text="Test notification")

        result = send_notification.apply(args=[notification.pk]).get()

        notification.refresh_from_db()
        self.assertEqual(result["status"], "error")
        self.assertEqual(notification.status, NotificationStatus.FAILED)
        self.assertNotIn("Provider detail", notification.error_message)
        self.assertEqual(send_email.call_count, 4)


class TelegramSubscriptionTests(TestCase):
    @patch.dict("os.environ", {"BOT_API_KEY": "test-bot-key"})
    def test_link_code_is_single_use_and_unsubscribe_removes_delivery_target(self):
        from .subscription_models import Subscription

        patient_user = get_user_model().objects.create(username="patient", role="patient")
        patient = patient_user.patient_profile
        client = APIClient()
        client.force_authenticate(patient_user)
        issue = client.post("/api/patients/telegram-link/")
        self.assertEqual(issue.status_code, 200)
        client.force_authenticate(None)
        headers = {"HTTP_X_BOT_KEY": "test-bot-key"}
        payload = {"chat_id": 1234, "code": issue.data["code"]}
        response = client.post("/api/bot/subscriptions/", payload, format="json", **headers)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(Subscription.objects.filter(patient=patient, is_active=True, is_verified=True).exists())
        self.assertEqual(client.post("/api/bot/subscriptions/", payload, format="json", **headers).status_code, 400)

        self.assertEqual(client.delete("/api/bot/subscriptions/1234/", **headers).status_code, 200)
        self.assertEqual(client.delete("/api/bot/subscriptions/1234/", **headers).status_code, 200)
        patient.refresh_from_db()
        self.assertEqual(patient.telegram_id, "")
        self.assertFalse(Subscription.objects.filter(patient=patient).exists())
