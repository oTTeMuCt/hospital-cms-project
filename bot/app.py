import os
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

logging.info("Starting Telegram bot placeholder")
logging.info("TELEGRAM_BOT_TOKEN set: %s", bool(TELEGRAM_BOT_TOKEN))
logging.info("REDIS_URL=%s", REDIS_URL)

try:
    while True:
        time.sleep(3600)
except KeyboardInterrupt:
    logging.info("Stopping Telegram bot placeholder")
