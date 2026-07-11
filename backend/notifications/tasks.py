import logging
import os

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification(self, notification_id: int) -> dict:
    """
    Отправляет уведомление по указанному каналу (telegram / email).
    Вызывается автоматически после создания Notification.
    """
    from .models import Notification, NotificationStatus

    try:
        notification = Notification.objects.select_related(
            "recipient_content_type"
        ).get(pk=notification_id)
    except Notification.DoesNotExist:
        logger.error("Notification pk=%s not found", notification_id)
        return {"status": "error", "detail": "Notification not found"}

    if notification.status != NotificationStatus.PENDING:
        logger.info("Notification pk=%s already processed (status=%s)", notification_id, notification.status)
        return {"status": "skipped", "detail": notification.status}

    channel = notification.channel
    try:
        if channel == "telegram":
            send_telegram(notification)
        elif channel == "email":
            send_email_notification(notification)
        else:
            logger.warning("Unknown channel %s for notification pk=%s", channel, notification_id)
            notification.status = NotificationStatus.FAILED
            notification.error_message = f"Unknown channel: {channel}"
            notification.save(update_fields=["status", "error_message"])
            return {"status": "error", "detail": f"Unknown channel: {channel}"}

        notification.status = NotificationStatus.SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=["status", "sent_at"])
        logger.info("Notification pk=%s sent via %s", notification_id, channel)
        return {"status": "sent", "channel": channel}

    except Exception as exc:
        logger.exception("Failed to send notification pk=%s via %s", notification_id, channel)
        notification.status = NotificationStatus.FAILED
        notification.error_message = str(exc)[:500]
        notification.save(update_fields=["status", "error_message"])
        raise self.retry(exc=exc)


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
    telegram_id = None

    # Попытка получить telegram_id из разных полей
    for attr in ("telegram_id", "telegram_chat_id", "chat_id"):
        telegram_id = getattr(recipient, attr, None)
        if telegram_id:
            break

    if not telegram_id:
        raise ValueError(f"Recipient {recipient} has no telegram_id")

    text = notification.subject and f"*{notification.subject}*\n{notification.text}" or notification.text

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": telegram_id,
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
