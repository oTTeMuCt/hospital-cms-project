"""
Hospital CMS Telegram Bot — notification subscription & analysis lookup.
Uses python-telegram-bot v21.x with JSON file persistence.
"""
import json
import logging
import os
import sys
from pathlib import Path
from threading import Lock

import requests
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

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
BOT_API_KEY = os.getenv("BOT_API_KEY", "HCMS-Bot-2024-Secret")
SUBSCRIPTIONS_FILE = Path(os.getenv("SUBSCRIPTIONS_FILE", "subscriptions.json"))

# Build the full analyses endpoint URL from the API base.
ANALYSES_URL = f"{API_BASE_URL.rstrip('/')}/bot/patient-analyses/"

REQUEST_TIMEOUT = 10  # seconds

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
        ["🔬 Мои анализы", "❌ Отписаться"],
        ["📖 Помощь"],
    ],
    resize_keyboard=True,
)

BACK_KEYBOARD = ReplyKeyboardMarkup(
    [["🏠 В главное меню"]],
    resize_keyboard=True,
)


# ---------------------------------------------------------------------------
# Helpers — API call
# ---------------------------------------------------------------------------

def _fetch_analyses(passport: str) -> dict:
    """Call the backend bot endpoint and return parsed JSON."""
    try:
        resp = requests.get(
            ANALYSES_URL,
            params={"passport": passport},
            headers={"X-Bot-Key": BOT_API_KEY},
            timeout=REQUEST_TIMEOUT,
        )
        # Force UTF-8 — slim containers lack locale info, so requests
        # may misdetect the charset and mangle Cyrillic text.
        resp.encoding = "utf-8"

        try:
            body = resp.json()
        except ValueError:
            logger.error(
                "Backend returned non-JSON response (status=%s). Body: %s",
                resp.status_code,
                resp.text[:2000],
            )
            return {
                "status_code": resp.status_code,
                "error": "Бэкенд вернул некорректный ответ. Попробуйте позже.",
            }

        return {"status_code": resp.status_code, **body}

    except requests.exceptions.Timeout:
        logger.error("Timeout fetching analyses for passport %s", passport)
        return {"status_code": 0, "error": "Сервер не отвечает. Попробуйте позже."}
    except requests.exceptions.ConnectionError:
        logger.error("Connection error fetching analyses for passport %s", passport)
        return {"status_code": 0, "error": "Не удалось подключиться к серверу."}
    except Exception as exc:
        logger.exception("Unexpected error fetching analyses for passport %s", passport)
        return {"status_code": 0, "error": "Произошла неизвестная ошибка. Попробуйте позже."}


def _format_analyses(data: dict) -> tuple[str, str]:
    """Return (text, parse_mode) for a nicely formatted analyses message."""
    if data.get("status_code") == 403:
        return "⚠️ <b>Доступ запрещён.</b>", "HTML"
    if data.get("error"):
        return f"⚠️ {data['error']}", "HTML"

    patient = data.get("patient", {})
    analyses = data.get("analyses", [])

    lines = [
        "🔬 <b>Результаты анализов</b>",
        "",
        f"👤 <b>Пациент:</b> {patient.get('full_name', '—')}",
        f"🎂 <b>Дата рождения:</b> {patient.get('birth_date', '—')}",
        f"⚥ <b>Пол:</b> {patient.get('gender', '—')}",
        "",
    ]

    if not analyses:
        lines.append("<i>Анализы не найдены.</i>")
        return "\n".join(lines), "HTML"

    lines.append(f"📊 <b>Найдено анализов: {len(analyses)}</b>")
    lines.append("")

    status_emoji = {
        "pending": "⏳",
        "in_progress": "🔬",
        "completed": "✅",
        "verified": "✔️",
        "cancelled": "❌",
    }

    for a in analyses:
        emoji = status_emoji.get(a.get("status"), "❓")
        lines.append(
            f"{emoji} <b>#{a.get('id')}</b> — {a.get('analysis_name', '—')}"
        )
        lines.append(f"   Статус: {a.get('status_display', '—')}")
        lines.append(f"   Запрошен: {a.get('requested_at', '—')[:10]}")

        if a.get("completed_at"):
            lines.append(f"   Завершён: {a['completed_at'][:10]}")

        if a.get("result"):
            lines.append(f"   📝 Результат: {a['result']}")

        if a.get("notes"):
            lines.append(f"   📌 Примечание: {a['notes']}")

        lines.append("")

    # Telegram has a 4096 char limit — truncate if needed with a note.
    full_text = "\n".join(lines)
    if len(full_text) > 4000:
        trunc_lines = lines[:50]
        trunc_lines.append("")
        trunc_lines.append("<i>⚠️ Слишком много данных. Показаны последние результаты.</i>")
        full_text = "\n".join(trunc_lines)

    return full_text, "HTML"


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.effective_user.first_name or "Гость"
    text = (
        f"🏥 <b>Hospital CMS</b> — Бот уведомлений\n\n"
        f"Здравствуйте, <b>{user_name}</b>!\n\n"
        f"Я помогу вам:\n"
        f"• 🔬 посмотреть результаты анализов\n"
        f"• 🔔 подписаться на уведомления\n\n"
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


async def ask_passport_for_analyses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask user to enter passport number / PINFL for analysis lookup."""
    text = (
        "🔬 <b>Мои анализы</b>\n\n"
        "Введите номер <b>паспорта</b> или <b>ПИНФЛ</b>, "
        "чтобы найти результаты ваших анализов.\n\n"
        "<i>Пример: AA1234567</i>"
    )
    context.user_data["awaiting_passport"] = True
    await update.message.reply_html(text, reply_markup=BACK_KEYBOARD)


async def handle_passport_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Call the backend API and display analysis results."""
    passport = update.message.text.strip()

    if not passport:
        await update.message.reply_html(
            "⚠️ Введите номер паспорта или ПИНФЛ.\n\nПопробуйте ещё раз:",
            reply_markup=BACK_KEYBOARD,
        )
        return

    context.user_data.pop("awaiting_passport", None)

    # Send a "typing" indicator while we wait for the backend.
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    logger.info("Looking up analyses for passport/PINFL: %s", passport)
    data = _fetch_analyses(passport)
    text, parse_mode = _format_analyses(data)

    if parse_mode == "HTML":
        await update.message.reply_html(text, reply_markup=MAIN_KEYBOARD)
    else:
        await update.message.reply_text(text, reply_markup=MAIN_KEYBOARD)


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📖 <b>Помощь</b>\n\n"
        "<b>📋 Мой профиль</b> — текущий статус подписки\n"
        "<b>🔔 Подписаться</b> — привязать ID пациента\n"
        "<b>🔬 Мои анализы</b> — результаты по паспорту/ПИНФЛ\n"
        "<b>❌ Отписаться</b> — отменить подписку\n"
        "<b>📖 Помощь</b> — это сообщение\n\n"
        "<i>По любым вопросам обращайтесь в регистратуру вашей клиники.</i>"
    )
    await update.message.reply_html(text, reply_markup=MAIN_KEYBOARD)


async def go_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("awaiting_patient_id", None)
    context.user_data.pop("awaiting_passport", None)
    await update.message.reply_html(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=MAIN_KEYBOARD,
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route text messages that aren't commands."""
    # Priority: if we're waiting for passport input (analyses lookup).
    if context.user_data.get("awaiting_passport"):
        await handle_passport_input(update, context)
        return

    # Patient ID input for subscription.
    if context.user_data.get("awaiting_patient_id"):
        await handle_patient_id_input(update, context)
        return

    text = update.message.text.strip()

    if text == "📋 Мой профиль":
        await show_profile(update, context)
    elif text == "🔔 Подписаться":
        await ask_patient_id(update, context)
    elif text == "🔬 Мои анализы":
        await ask_passport_for_analyses(update, context)
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
    app.add_handler(CommandHandler("analyses", ask_passport_for_analyses))

    # Text messages (keyboard buttons + input states)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.add_error_handler(error_handler)

    logger.info("Telegram bot starting (polling mode)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
