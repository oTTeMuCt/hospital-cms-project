import logging
import os

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from patients.models import Patient

from .models import Notification, NotificationChannel, NotificationStatus
from .subscription_models import Subscription

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
@transaction.atomic
def send_notification(self, notification_id: int) -> dict:
    """Deliver a queued notification and retry transient delivery errors."""
    try:
        notification = Notification.objects.select_for_update().get(pk=notification_id)
    except Notification.DoesNotExist:
        logger.error("Notification pk=%s not found", notification_id)
        return {"status": "error", "detail": "Notification not found"}

    if notification.status != NotificationStatus.PENDING:
        logger.info("Notification pk=%s already processed (status=%s)", notification_id, notification.status)
        return {"status": "skipped", "detail": notification.status}

    channel = notification.channel
    senders = {
        NotificationChannel.EMAIL: send_email_notification,
        NotificationChannel.TELEGRAM: send_telegram,
    }
    sender = senders.get(channel)
    if sender is None:
        error_message = "Notification channel is unsupported."
    else:
        try:
            sender(notification)
        except Exception as exc:
            # Provider errors can contain credentials, recipient details or message text.
            logger.warning(
                "Notification %s failed on attempt %s (%s)",
                notification_id, self.request.retries + 1, type(exc).__name__,
            )
            if self.request.retries < self.max_retries:
                raise self.retry() from None
            error_message = "Notification delivery failed after retries."
        else:
            notification.status = NotificationStatus.SENT
            notification.sent_at = timezone.now()
            notification.error_message = ""
            notification.save(update_fields=["status", "sent_at", "error_message"])
            return {"status": "sent", "channel": channel}

    notification.status = NotificationStatus.FAILED
    notification.error_message = error_message
    notification.save(update_fields=["status", "error_message"])
    return {"status": "error", "detail": error_message}


def send_telegram(notification) -> None:
    """
    Отправляет сообщение через Telegram Bot API.
    Использует TELEGRAM_BOT_TOKEN из настроек.
    Получатель должен иметь telegram_id в своём профиле (Patient.telegram_id / User.telegram_id).
    """
    import requests  # lazy import; requests должен быть доступен

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    recipient = notification.recipient
    if not isinstance(recipient, Patient):
        raise ValueError("Telegram notifications require a patient recipient")
    subscription = Subscription.objects.select_for_update().filter(
        patient=recipient, is_active=True, is_verified=True,
    ).first()
    if subscription is None:
        raise ValueError("Recipient has no verified Telegram subscription")

    text = notification.subject and f"*{notification.subject}*\n{notification.text}" or notification.text

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": subscription.chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")


def send_email_notification(notification) -> None:
    """
    Отправляет email через Django SMTP.
    Получатель должен иметь поле email.
    """
    recipient = notification.recipient
    email = getattr(recipient, "email", None)
    if not email:
        raise ValueError(f"Recipient {recipient} has no email")

    send_mail(
        subject=notification.subject or "Уведомление HCMS",
        message=notification.text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
