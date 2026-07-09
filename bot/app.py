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

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

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
    logger.critical("TELEGRAM_BOT_TOKEN is not set. Exiting.")
    sys.exit(1)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
SUBSCRIPTIONS_FILE = Path(os.getenv("SUBSCRIPTIONS_FILE", "subscriptions.json"))

# ---------------------------------------------------------------------------
# Subscription store
# ---------------------------------------------------------------------------

_subscriptions: dict[int, str] = {}
_lock = Lock()


def _load_subscriptions() -> None:
    global _subscriptions
    if SUBSCRIPTIONS_FILE.exists():
        try:
            raw = SUBSCRIPTIONS_FILE.read_text(encoding="utf-8")
            _subscriptions = {int(k): v for k, v in json.loads(raw).items()}
            logger.info("Loaded %d subscription(s)", len(_subscriptions))
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            logger.warning("Failed to load subscriptions: %s", exc)
            _subscriptions = {}
    else:
        logger.info("No existing subscriptions — starting fresh.")


def _save_subscriptions() -> None:
    with _lock:
        data = {str(k): v for k, v in _subscriptions.items()}
    try:
        SUBSCRIPTIONS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as exc:
        logger.error("Failed to save subscriptions: %s", exc)


# ---------------------------------------------------------------------------
# Keyboard layouts
# ---------------------------------------------------------------------------

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📋 Мой профиль", "🔔 Подписаться"],
        ["❌ Отписаться", "📖 Помощь"],
    ],
    resize_keyboard=True,
    persistent=True,
)

BACK_KEYBOARD = ReplyKeyboardMarkup(
    [["🏠 В главное меню"]],
    resize_keyboard=True,
    persistent=True,
)

# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.effective_user.first_name or "Гость"
    text = (
        f"🏥 <b>Hospital CMS</b> — Бот уведомлений\n\n"
        f"Здравствуйте, <b>{user_name}</b>!\n\n"
        f"Я помогу вам получать уведомления о пациентах:\n"
        f"• результаты анализов\n"
        f"• записи на приём\n"
        f"• изменения в карточке\n\n"
        f"<i>Используйте кнопки меню ниже ↓</i>"
    )
    await update.message.reply_html(text, reply_markup=MAIN_KEYBOARD)


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name or "Пользователь"

    with _lock:
        patient_id = _subscriptions.get(chat_id)

    if patient_id:
        text = (
            f"👤 <b>Ваш профиль</b>\n\n"
            f"▫️ Telegram: {user_name}\n"
            f"▫️ Chat ID: <code>{chat_id}</code>\n"
            f"▫️ Привязан к пациенту: <b>#{patient_id}</b>\n\n"
            f"✅ <i>Вы получаете уведомления</i>"
        )
    else:
        text = (
            f"👤 <b>Ваш профиль</b>\n\n"
            f"▫️ Telegram: {user_name}\n"
            f"▫️ Chat ID: <code>{chat_id}</code>\n\n"
            f"⚠️ <i>Нет активных подписок</i>\n"
            f"Нажмите «🔔 Подписаться» чтобы подключить уведомления."
        )

    await update.message.reply_html(text, reply_markup=MAIN_KEYBOARD)


async def ask_patient_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🔔 <b>Подписка на уведомления</b>\n\n"
        "Введите <b>ID пациента</b>, чтобы получать уведомления "
        "о его анализах, приёмах и изменениях.\n\n"
        "<i>ID можно узнать у вашего врача или в личном кабинете HCMS.</i>"
    )
    context.user_data["awaiting_patient_id"] = True
    await update.message.reply_html(text, reply_markup=BACK_KEYBOARD)


async def handle_patient_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get("awaiting_patient_id"):
        return

    patient_id = update.message.text.strip()

    if not patient_id.isdigit():
        await update.message.reply_html(
            "⚠️ ID пациента должен состоять из цифр.\n\nПопробуйте ещё раз:",
            reply_markup=BACK_KEYBOARD,
        )
        return

    chat_id = update.effective_chat.id
    with _lock:
        _subscriptions[chat_id] = patient_id
    _save_subscriptions()
    context.user_data.pop("awaiting_patient_id", None)

    logger.info("Chat %d subscribed to patient %s", chat_id, patient_id)

    await update.message.reply_html(
        f"✅ <b>Подписка оформлена!</b>\n\n"
        f"Теперь вы будете получать уведомления для <b>Пациента #{patient_id}</b>.\n\n"
        f"📋 Проверьте статус в разделе «Мой профиль».",
        reply_markup=MAIN_KEYBOARD,
    )


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    with _lock:
        patient_id = _subscriptions.pop(chat_id, None)

    if patient_id:
        _save_subscriptions()
        logger.info("Chat %d unsubscribed from patient %s", chat_id, patient_id)
        await update.message.reply_html(
            f"🗑️ <b>Подписка отменена</b>\n\n"
            f"Вы больше не получаете уведомления для <b>Пациента #{patient_id}</b>.",
            reply_markup=MAIN_KEYBOARD,
        )
    else:
        await update.message.reply_html(
            "ℹ️ У вас нет активных подписок.\n\n"
            "Нажмите «🔔 Подписаться» чтобы начать.",
            reply_markup=MAIN_KEYBOARD,
        )


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📖 <b>Помощь</b>\n\n"
        "<b>📋 Мой профиль</b> — текущий статус подписки\n"
        "<b>🔔 Подписаться</b> — привязать ID пациента\n"
        "<b>❌ Отписаться</b> — отменить подписку\n"
        "<b>📖 Помощь</b> — это сообщение\n\n"
        "<i>По любым вопросам обращайтесь в регистратуру вашей клиники.</i>"
    )
    await update.message.reply_html(text, reply_markup=MAIN_KEYBOARD)


async def go_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("awaiting_patient_id", None)
    await update.message.reply_html(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=MAIN_KEYBOARD,
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route text messages that aren't commands."""
    if context.user_data.get("awaiting_patient_id"):
        await handle_patient_id_input(update, context)
        return

    text = update.message.text.strip()

    if text == "📋 Мой профиль":
        await show_profile(update, context)
    elif text == "🔔 Подписаться":
        await ask_patient_id(update, context)
    elif text == "❌ Отписаться":
        await unsubscribe(update, context)
    elif text == "📖 Помощь":
        await show_help(update, context)
    elif text == "🏠 В главное меню":
        await go_main_menu(update, context)
    else:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки меню ↓",
            reply_markup=MAIN_KEYBOARD,
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception handling update: %s", context.error, exc_info=True)
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="😞 Произошла ошибка. Попробуйте ещё раз.",
                reply_markup=MAIN_KEYBOARD,
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def main() -> None:
    _load_subscriptions()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("profile", show_profile))
    app.add_handler(CommandHandler("subscribe", ask_patient_id))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(CommandHandler("help", show_help))

    # Text messages (keyboard buttons + patient ID input)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.add_error_handler(error_handler)

    logger.info("Telegram bot starting (polling mode)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
