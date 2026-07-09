"""
Hospital CMS Telegram Bot — notification subscription management.
Uses python-telegram-bot v21.x with JSON file persistence.
"""
import json
import logging
import os
import sys
from pathlib import Path
from threading import Lock

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("telegram_bot")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.critical("TELEGRAM_BOT_TOKEN environment variable is not set. Exiting.")
    sys.exit(1)

# Optional: backend API base URL for future integration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# Where we persist chat_id -> patient_id mappings
SUBSCRIPTIONS_FILE = Path(os.getenv("SUBSCRIPTIONS_FILE", "subscriptions.json"))

# ---------------------------------------------------------------------------
# Subscription store — in-memory dict backed by a JSON file
# ---------------------------------------------------------------------------

_subscriptions: dict[int, str] = {}       # chat_id -> patient_id
_lock = Lock()


def _load_subscriptions() -> None:
    """Load subscriptions from the JSON file into the in-memory dict (thread-safe)."""
    global _subscriptions
    if SUBSCRIPTIONS_FILE.exists():
        try:
            raw = SUBSCRIPTIONS_FILE.read_text(encoding="utf-8")
            # JSON keys are always strings, so cast them back to ints
            _subscriptions = {int(k): v for k, v in json.loads(raw).items()}
            logger.info("Loaded %d subscription(s) from %s", len(_subscriptions), SUBSCRIPTIONS_FILE)
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            logger.warning("Could not load subscriptions file (%s): %s", SUBSCRIPTIONS_FILE, exc)
            _subscriptions = {}
    else:
        logger.info("No existing subscriptions file — starting fresh.")


def _save_subscriptions() -> None:
    """Persist the in-memory dict to JSON (thread-safe)."""
    with _lock:
        data = {str(k): v for k, v in _subscriptions.items()}
    try:
        SUBSCRIPTIONS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as exc:
        logger.error("Failed to save subscriptions to %s: %s", SUBSCRIPTIONS_FILE, exc)


# ---------------------------------------------------------------------------
# Bot command handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message."""
    welcome = (
        "🏥 <b>Hospital CMS Notification Bot</b> 🏥\n\n"
        "I can notify you about updates for patients you're subscribed to.\n\n"
        "<b>Available commands:</b>\n"
        "  /subscribe <code><patient_id></code> — subscribe to a patient's notifications\n"
        "  /unsubscribe — cancel your subscription\n"
        "  /status — show your current subscription\n\n"
        "Use /subscribe followed by a patient ID to get started!"
    )
    await update.message.reply_html(welcome)


async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Register the current chat with a patient profile.

    Usage: /subscribe <patient_id>
    """
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "⚠️  Please provide a patient ID.\n\n"
            "Usage: /subscribe <code><patient_id></code>",
            parse_mode="HTML",
        )
        return

    patient_id = context.args[0].strip()
    chat_id = update.effective_chat.id

    with _lock:
        _subscriptions[chat_id] = patient_id

    _save_subscriptions()

    logger.info("Chat %d subscribed to patient %s", chat_id, patient_id)
    await update.message.reply_text(
        f"✅ You are now subscribed to notifications for <b>Patient {patient_id}</b>.",
        parse_mode="HTML",
    )


async def cmd_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the current chat's subscription."""
    chat_id = update.effective_chat.id

    removed = False
    with _lock:
        if chat_id in _subscriptions:
            patient_id = _subscriptions.pop(chat_id)
            removed = True
            logger.info("Chat %d unsubscribed from patient %s", chat_id, patient_id)

    if removed:
        _save_subscriptions()
        await update.message.reply_text(
            f"🗑️  You have been unsubscribed from <b>Patient {patient_id}</b>.",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("ℹ️  You don't have an active subscription.")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the current subscription for the chat."""
    chat_id = update.effective_chat.id

    with _lock:
        patient_id = _subscriptions.get(chat_id)

    if patient_id:
        await update.message.reply_text(
            f"📋  You are currently subscribed to <b>Patient {patient_id}</b>.",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            "📭  You are not subscribed to any patient.\n\n"
            "Use /subscribe <code><patient_id></code> to start receiving notifications.",
            parse_mode="HTML",
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors gracefully."""
    logger.error("Exception while handling update %s: %s", update, context.error, exc_info=True)
    # If we have a chat to reply to, let the user know something went wrong
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="😞  Sorry, something went wrong. Please try again later.",
            )
        except Exception:
            pass  # best-effort


# ---------------------------------------------------------------------------
# Application bootstrap
# ---------------------------------------------------------------------------

def main() -> None:
    """Build and run the bot."""
    # Load any existing subscriptions before the bot starts
    _load_subscriptions()

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Register command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("subscribe", cmd_subscribe))
    app.add_handler(CommandHandler("unsubscribe", cmd_unsubscribe))
    app.add_handler(CommandHandler("status", cmd_status))

    # Global error handler
    app.add_error_handler(error_handler)

    logger.info("Telegram bot starting (polling mode)…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()