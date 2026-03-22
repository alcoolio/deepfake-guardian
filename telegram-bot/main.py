"""Telegram moderation bot entry-point.

Listens for text messages, photos, and videos in group chats, sends them to
the moderation engine, and acts on the verdict (delete or notify admins).
"""

from __future__ import annotations

import logging

import structlog
from telegram import Message, Update
from telegram.constants import ChatMemberStatus, ChatType
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters,
)

import engine_client
from config import settings
from i18n.loader import get_message

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logging.basicConfig(format="%(message)s", level=logging.INFO)
logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _bot_is_admin(message: Message) -> bool:
    """Check whether the bot has delete permissions in this chat."""
    chat = message.chat
    if chat.type == ChatType.PRIVATE:
        return False
    me = await message.get_bot().get_me()
    member = await chat.get_chat_member(me.id)
    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)


async def _notify_admins(
    message: Message, reasons: list[str], language: str = "en"
) -> None:
    """Mention group admins about a flagged message, in the detected language."""
    admins = await message.chat.get_administrators()
    mentions = " ".join(f"@{a.user.username}" for a in admins if a.user.username)
    reason_text = ", ".join(reasons)

    if mentions:
        msg = get_message("flagged_content", language, reasons=reason_text, mentions=mentions)
    else:
        msg = get_message("flagged_content_no_admins", language, reasons=reason_text)

    await message.reply_text(msg)


async def _handle_verdict(
    message: Message, result: dict, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Delete the message or notify admins based on the engine verdict."""
    verdict = result.get("verdict", "allow")
    reasons = result.get("reasons", [])
    language = result.get("language") or settings.bot_language

    if verdict == "allow":
        return

    logger.info(
        "moderation_action",
        verdict=verdict,
        reasons=reasons,
        language=language,
        chat_id=message.chat_id,
        message_id=message.message_id,
    )

    if verdict == "delete":
        if await _bot_is_admin(message):
            await message.delete()
            logger.info("message_deleted", message_id=message.message_id)
        else:
            await _notify_admins(message, reasons, language)
    elif verdict == "flag":
        await _notify_admins(message, reasons, language)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages."""
    message = update.effective_message
    if message is None or message.text is None:
        return
    try:
        result = await engine_client.moderate_text(message.text)
        await _handle_verdict(message, result, context)
    except Exception:
        logger.exception("text_moderation_error")


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming photos."""
    message = update.effective_message
    if message is None or not message.photo:
        return
    try:
        photo = message.photo[-1]  # highest resolution
        file = await photo.get_file()
        data = await file.download_as_bytearray()
        result = await engine_client.moderate_image(bytes(data))
        await _handle_verdict(message, result, context)
    except Exception:
        logger.exception("image_moderation_error")


async def on_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming videos."""
    message = update.effective_message
    if message is None or message.video is None:
        return
    try:
        file = await message.video.get_file()
        data = await file.download_as_bytearray()
        result = await engine_client.moderate_video(bytes(data))
        await _handle_verdict(message, result, context)
    except Exception:
        logger.exception("video_moderation_error")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not settings.bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    app = Application.builder().token(settings.bot_token).build()

    # Only react to group messages (not private chats)
    group_filter = filters.ChatType.GROUPS

    app.add_handler(MessageHandler(filters.TEXT & group_filter & ~filters.COMMAND, on_text))
    app.add_handler(MessageHandler(filters.PHOTO & group_filter, on_photo))
    app.add_handler(MessageHandler(filters.VIDEO & group_filter, on_video))

    logger.info("telegram_bot_started", engine_url=settings.engine_url)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
