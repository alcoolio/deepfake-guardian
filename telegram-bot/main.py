"""Telegram moderation bot entry-point.

Listens for text messages, photos, and videos in group chats, sends them to
the moderation engine, and acts on the verdict (delete or notify admins).

Phase 3 additions:
- Warning / escalation system integrated into _handle_verdict().
- /privacy command: show GDPR privacy notice.
- /delete_my_data command: submit Article 17 erasure request.
"""
from __future__ import annotations

import logging

import structlog
from telegram import Message, Update
from telegram.constants import ChatMemberStatus, ChatType
from telegram.ext import (
    Application,
    CommandHandler,
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


async def _handle_warning(
    message: Message,
    reasons: list[str],
    language: str,
) -> None:
    """Record a violation and send the appropriate escalation message.

    Escalation levels:
      notice               — educational reply in the group
      admin_notification   — reply mentioning admins
      supervisor_escalation — reply mentioning admins with urgency marker
    """
    sender = message.from_user
    if sender is None:
        return

    user_id = str(sender.id)
    group_id = str(message.chat_id)

    try:
        warn_result = await engine_client.record_warning(user_id, group_id, reasons)
    except Exception:
        logger.exception("warning_record_failed")
        return

    action = warn_result.get("action", "notice")
    count = warn_result.get("warning_count", 1)
    reason_text = ", ".join(reasons)
    mention = f"@{sender.username}" if sender.username else sender.first_name

    admins = await message.chat.get_administrators()
    admin_mentions = " ".join(f"@{a.user.username}" for a in admins if a.user.username)

    if action == "notice":
        msg = get_message("warning_notice", language, reasons=reason_text)
        await message.reply_text(msg)

    elif action == "admin_notification":
        if admin_mentions:
            msg = get_message(
                "warning_admin_notification",
                language,
                mention=mention,
                reasons=reason_text,
                admin_mentions=admin_mentions,
            )
        else:
            msg = get_message(
                "warning_admin_notification_no_admins",
                language,
                reasons=reason_text,
                count=count,
            )
        await message.reply_text(msg)

    elif action == "supervisor_escalation":
        if admin_mentions:
            msg = get_message(
                "warning_supervisor_escalation",
                language,
                mention=mention,
                reasons=reason_text,
                count=count,
                admin_mentions=admin_mentions,
            )
        else:
            msg = get_message(
                "warning_supervisor_escalation_no_admins",
                language,
                reasons=reason_text,
                count=count,
            )
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
        # Record violation and apply escalation after deletion
        await _handle_warning(message, reasons, language)

    elif verdict == "flag":
        await _notify_admins(message, reasons, language)
        # Also track flagged content as a violation
        await _handle_warning(message, reasons, language)


# ---------------------------------------------------------------------------
# Message handlers
# ---------------------------------------------------------------------------

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages."""
    message = update.effective_message
    if message is None or message.text is None:
        return
    try:
        sender = message.from_user
        user_id = str(sender.id) if sender else None
        group_id = str(message.chat_id)
        result = await engine_client.moderate_text(message.text, user_id=user_id, group_id=group_id)
        await _handle_verdict(message, result, context)
    except Exception:
        logger.exception("text_moderation_error")


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming photos."""
    message = update.effective_message
    if message is None or not message.photo:
        return
    try:
        sender = message.from_user
        user_id = str(sender.id) if sender else None
        group_id = str(message.chat_id)
        photo = message.photo[-1]  # highest resolution
        file = await photo.get_file()
        data = await file.download_as_bytearray()
        result = await engine_client.moderate_image(bytes(data), user_id=user_id, group_id=group_id)
        await _handle_verdict(message, result, context)
    except Exception:
        logger.exception("image_moderation_error")


async def on_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming videos."""
    message = update.effective_message
    if message is None or message.video is None:
        return
    try:
        sender = message.from_user
        user_id = str(sender.id) if sender else None
        group_id = str(message.chat_id)
        file = await message.video.get_file()
        data = await file.download_as_bytearray()
        result = await engine_client.moderate_video(bytes(data), user_id=user_id, group_id=group_id)
        await _handle_verdict(message, result, context)
    except Exception:
        logger.exception("video_moderation_error")


# ---------------------------------------------------------------------------
# GDPR commands
# ---------------------------------------------------------------------------

async def cmd_privacy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/privacy — show the privacy notice to the requesting user."""
    message = update.effective_message
    if message is None:
        return
    lang = settings.bot_language
    await message.reply_text(
        get_message("privacy_notice", lang),
        parse_mode="Markdown",
    )


async def cmd_delete_my_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/delete_my_data — submit an Article 17 erasure request."""
    message = update.effective_message
    if message is None:
        return

    sender = message.from_user
    if sender is None:
        return

    lang = settings.bot_language
    user_id = str(sender.id)

    try:
        result = await engine_client.gdpr_delete_request(user_id)
        req_id = result.get("request_id", "?")

        # Different message if a request was already pending
        if "already pending" in result.get("message", "").lower():
            msg = get_message("delete_my_data_already_pending", lang, request_id=req_id)
        else:
            msg = get_message("delete_my_data_submitted", lang, request_id=req_id)
    except Exception:
        logger.exception("gdpr_delete_request_failed", user_id=user_id)
        msg = get_message("delete_my_data_error", lang)

    await message.reply_text(msg)


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

    # GDPR commands — work in both groups and private chats
    app.add_handler(CommandHandler("privacy", cmd_privacy))
    app.add_handler(CommandHandler("delete_my_data", cmd_delete_my_data))

    logger.info("telegram_bot_started", engine_url=settings.engine_url)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
