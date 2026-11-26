"""
Hospital CMS Telegram Bot — notification subscription & analysis lookup.
Uses python-telegram-bot v21.x with database persistence for subscriptions.

IMPORTANT: This bot uses a singleton lock file to prevent multiple polling instances.
Do NOT run multiple copies of this bot simultaneously.
"""
import asyncio
import logging
import os
import sys
import tempfile
from html import escape
from threading import Lock
from dotenv import load_dotenv

import requests
from telegram import ReplyKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ---------------------------------------------------------------------------
# Singleton lock — prevents multiple bot instances (Issue 15)
# ---------------------------------------------------------------------------
load_dotenv()
_LOCK_FILE = os.path.join(tempfile.gettempdir(), "hospital_cms_bot.lock")


def _acquire_singleton_lock() -> bool:
    """
    Attempt to acquire a singleton lock file.
    Returns True if lock was acquired, False if another instance is running.
    """
    try:
        # Use a file-based lock via atomic create
        if os.path.exists(_LOCK_FILE):
            # Check if lock is stale (process no longer running)
            try:
                with open(_LOCK_FILE, "r") as f:
                    pid = int(f.read().strip())
                # Check if process exists on Windows
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(0x1000, False, pid)
                if handle:
                    kernel32.CloseHandle(handle)
                    logger.error("Another bot instance is running (PID: %d). Exiting.", pid)
                    return False
                else:
                    # Stale lock — remove it
                    os.remove(_LOCK_FILE)
            except (ValueError, OSError, AttributeError):
                # Can't read or check PID — assume stale
                try:
                    os.remove(_LOCK_FILE)
                except OSError:
                    pass

        with open(_LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        logger.info("Bot singleton lock acquired (PID: %d)", os.getpid())
        return True
    except Exception as exc:
        logger.warning("Could not acquire singleton lock: %s", exc)
        return True  # Allow startup even if lock fails


def _release_singleton_lock() -> None:
    """Release the singleton lock file."""
    try:
        if os.path.exists(_LOCK_FILE):
            with open(_LOCK_FILE, "r") as f:
                pid = int(f.read().strip())
                if pid == os.getpid():
                    os.remove(_LOCK_FILE)
                    logger.info("Bot singleton lock released.")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("telegram_bot")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.critical("TELEGRAM_BOT_TOKEN is not set. Exiting.")
    sys.exit(1)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
BOT_API_KEY = os.getenv("BOT_API_KEY")
if not BOT_API_KEY:
    logger.critical("BOT_API_KEY is not set. Exiting.")
    sys.exit(1)

# Build the full analyses endpoint URL from the API base.
ANALYSES_URL = f"{API_BASE_URL.rstrip('/')}/bot/patient-analyses/"
SUBSCRIPTIONS_URL = f"{API_BASE_URL.rstrip('/')}/bot/subscriptions/"

REQUEST_TIMEOUT = 10  # seconds

# ---------------------------------------------------------------------------
# Subscription store — uses backend API for persistence (Issue 16)
# ---------------------------------------------------------------------------

_subscriptions: dict[int, str] = {}
_lock = Lock()


def _load_subscriptions_from_api() -> None:
    """Fetch subscriptions from the backend database instead of JSON file."""
    global _subscriptions
    try:
        resp = requests.get(
            SUBSCRIPTIONS_URL,
            headers={"X-Bot-Key": BOT_API_KEY},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            with _lock:
                _subscriptions = {}
                for sub in data:
                    chat_id = sub.get("chat_id")
                    patient_id = sub.get("patient_id_str") or sub.get("patient_id")
                    if chat_id and patient_id:
                        _subscriptions[int(chat_id)] = str(patient_id)
            logger.info("Loaded %d subscription(s) from API", len(_subscriptions))
        else:
            logger.warning("Failed to load subscriptions from API (status=%s)", resp.status_code)
            with _lock:
                _subscriptions = {}
    except requests.exceptions.ConnectionError:
        logger.warning("Cannot connect to backend API — subscriptions will be empty.")
        with _lock:
            _subscriptions = {}
    except Exception as exc:
        logger.warning("Failed to load subscriptions from API: %s", exc)
        with _lock:
            _subscriptions = {}


def _save_subscription_to_api(chat_id: int, code: str) -> dict:
    """Save a subscription to the backend via API."""
    try:
        resp = requests.post(
            SUBSCRIPTIONS_URL,
            json={"chat_id": chat_id, "code": code},
            headers={"X-Bot-Key": BOT_API_KEY, "Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code in (200, 201):
            return resp.json()
        if resp.status_code == 409:
            return {"error": "Сначала отмените предыдущую подписку."}
        if resp.status_code == 400:
            return {"error": "Код недействителен или истёк. Получите новый код в личном кабинете."}
        return {"error": "Не удалось подключить подписку. Попробуйте позже."}
    except Exception as exc:
        logger.error("Error saving subscription (%s)", type(exc).__name__)
        return {"error": "Не удалось подключить подписку. Попробуйте позже."}


def _delete_subscription_from_api(chat_id: int) -> dict:
    """Delete a subscription from the backend via API."""
    try:
        resp = requests.delete(
            f"{SUBSCRIPTIONS_URL.rstrip('/')}/{chat_id}/",
            headers={"X-Bot-Key": BOT_API_KEY},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code in (200, 204):
            return {"status": "ok"}
        logger.warning("Failed to delete subscription (status=%s)", resp.status_code)
        return {"error": "Не удалось отменить подписку. Попробуйте позже."}
    except Exception as exc:
        logger.error("Error deleting subscription (%s)", type(exc).__name__)
        return {"error": "Не удалось отменить подписку. Попробуйте позже."}


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

def _fetch_analyses(chat_id: int, identifier: str) -> dict:
    """Look up published results for the verified chat."""
    identifier_field = "pinfl" if len(identifier) == 14 and identifier.isascii() and identifier.isdecimal() else "passport"
    try:
        resp = requests.post(
            ANALYSES_URL,
            json={"chat_id": chat_id, identifier_field: identifier},
            headers={"X-Bot-Key": BOT_API_KEY},
            timeout=REQUEST_TIMEOUT,
        )
        resp.encoding = "utf-8"

        try:
            body = resp.json()
        except ValueError:
            logger.error(
                "Backend returned non-JSON response (status=%s)",
                resp.status_code,
            )
            return {
                "status_code": resp.status_code,
                "error": "Бэкенд вернул некорректный ответ. Попробуйте позже.",
            }

        return {"status_code": resp.status_code, **body}

    except requests.exceptions.Timeout:
        logger.error("Timeout fetching analyses")
        return {"status_code": 0, "error": "Сервер не отвечает. Попробуйте позже."}
    except requests.exceptions.ConnectionError:
        logger.error("Connection error fetching analyses")
        return {"status_code": 0, "error": "Не удалось подключиться к серверу."}
    except Exception as exc:
        logger.error("Unexpected error fetching analyses (%s)", type(exc).__name__)
        return {"status_code": 0, "error": "Произошла неизвестная ошибка. Попробуйте позже."}


def _format_analyses(data: dict) -> tuple[str, str]:
    if data.get("error"):
        return "⚠️ " + escape(str(data["error"])), "HTML"

    patient = data.get("patient", {})
    analyses = data.get("analyses", [])
    lines = [
        "🔬 <b>Результаты анализов</b>",
        f"Пациент: {escape(str(patient.get('full_name', '—')))}",
        "",
    ]
    if not analyses:
        lines.append("Опубликованных анализов пока нет.")

    for result in analyses:
        lines.append(f"<b>{escape(str(result.get('analysis_name', '—')))}</b>")
        fields = result.get("result_fields") or []
        if fields:
            for field in fields:
                parts = [
                    f"{field.get('field_name', '')}: {field.get('value', '')}",
                    field.get("unit"), field.get("interpretation"), field.get("reference_range_text"),
                ]
                lines.append(escape(" · ".join(str(part) for part in parts if part)))
        elif result.get("result"):
            lines.extend(escape(str(result["result"])).splitlines())
        lines.append("")

    visible = []
    length = 0
    for line in lines:
        length += len(line.encode("utf-16-le")) // 2 + 1
        if length > 3900:
            visible.append("Показана часть результатов. Остальные доступны в личном кабинете.")
            break
        visible.append(line)
    return "\n".join(visible), "HTML"


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = escape(update.effective_user.first_name or "Гость")
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
    user_name = escape(update.effective_user.first_name or "Пользователь")

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
    context.user_data.pop("awaiting_passport", None)
    context.user_data["awaiting_patient_id"] = True
    await update.message.reply_html(
        "Получите одноразовый код в профиле пациента Hospital CMS и отправьте его сюда.",
        reply_markup=BACK_KEYBOARD,
    )


async def handle_patient_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    code = update.message.text.strip()
    if not code:
        return
    chat_id = update.effective_chat.id
    result = await asyncio.to_thread(_save_subscription_to_api, chat_id, code)
    if result.get("error"):
        await update.message.reply_text(result["error"], reply_markup=BACK_KEYBOARD)
        return

    with _lock:
        _subscriptions[chat_id] = str(result["patient_id"])
    context.user_data.pop("awaiting_patient_id", None)
    await update.message.reply_html("✅ <b>Подписка оформлена.</b>", reply_markup=MAIN_KEYBOARD)


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    result = await asyncio.to_thread(_delete_subscription_from_api, chat_id)
    if result.get("error"):
        await update.message.reply_text(result["error"], reply_markup=MAIN_KEYBOARD)
        return
    with _lock:
        _subscriptions.pop(chat_id, None)
    await update.message.reply_html("🗑️ <b>Подписка отменена.</b>", reply_markup=MAIN_KEYBOARD)


async def ask_passport_for_analyses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask user to enter passport number / PINFL for analysis lookup."""
    text = (
        "🔬 <b>Мои анализы</b>\n\n"
        "Введите номер <b>паспорта</b> или <b>ПИНФЛ</b>, "
        "чтобы найти результаты ваших анализов.\n\n"
        "<i>Пример: AA1234567</i>"
    )
    context.user_data.pop("awaiting_patient_id", None)
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

    data = await asyncio.to_thread(_fetch_analyses, update.effective_chat.id, passport)
    text, parse_mode = _format_analyses(data)

    if parse_mode == "HTML":
        await update.message.reply_html(text, reply_markup=MAIN_KEYBOARD)
    else:
        await update.message.reply_text(text, reply_markup=MAIN_KEYBOARD)


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📖 <b>Помощь</b>\n\n"
        "<b>📋 Мой профиль</b> — текущий статус подписки\n"
        "<b>🔔 Подписаться</b> — ввести одноразовый код из личного кабинета\n"
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
    text = update.message.text.strip()
    if text == "🏠 В главное меню":
        await go_main_menu(update, context)
        return

    if context.user_data.get("awaiting_passport"):
        await handle_passport_input(update, context)
        return

    if context.user_data.get("awaiting_patient_id"):
        await handle_patient_id_input(update, context)
        return

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
    else:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки меню ↓",
            reply_markup=MAIN_KEYBOARD,
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception handling update (%s)", type(context.error).__name__)
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
    if not _acquire_singleton_lock():
        sys.exit(1)

    try:
        _load_subscriptions_from_api()

        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Commands
        app.add_handler(CommandHandler("start", cmd_start, filters=filters.ChatType.PRIVATE))
        app.add_handler(CommandHandler("profile", show_profile, filters=filters.ChatType.PRIVATE))
        app.add_handler(CommandHandler("subscribe", ask_patient_id, filters=filters.ChatType.PRIVATE))
        app.add_handler(CommandHandler("unsubscribe", unsubscribe, filters=filters.ChatType.PRIVATE))
        app.add_handler(CommandHandler("help", show_help, filters=filters.ChatType.PRIVATE))
        app.add_handler(CommandHandler("analyses", ask_passport_for_analyses, filters=filters.ChatType.PRIVATE))

        # Text messages (keyboard buttons + input states)
        app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, handle_text))

        app.add_error_handler(error_handler)

        logger.info("Telegram bot starting (polling mode)...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except TelegramError as exc:
        logger.error("Telegram polling stopped (%s)", type(exc).__name__)
        raise SystemExit(1) from None
    finally:
        _release_singleton_lock()


if __name__ == "__main__":
    main()