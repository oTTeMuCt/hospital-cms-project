import os

from django.utils.crypto import constant_time_compare

TELEGRAM_LINK_SALT = "patients.telegram-link"
TELEGRAM_LINK_TTL = 600


def is_bot_request(request):
    expected_key = os.getenv("BOT_API_KEY")
    return bool(expected_key and constant_time_compare(request.headers.get("X-Bot-Key", ""), expected_key))
