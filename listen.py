import logging
import os

from typing import Optional, Tuple
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# ---- logging ----
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


# -------- helpers --------
def _extract_text(update: Update) -> Tuple[Optional[int], Optional[str]]:
    """Return (chat_id, text_or_caption) from any update type."""
    chat = update.effective_chat
    msg = update.effective_message  # works for message, edited_message, channel_post, etc.
    chat_id = chat.id if chat else None
    text = None
    if msg:
        # text for text messages, caption for media posts
        text = msg.text or msg.caption
        if isinstance(text, str):
            text = text.strip()
    return chat_id, text


# -------- handlers --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id, _ = _extract_text(update)
    logger.info("Received /start from user=%s chat_id=%s", getattr(user, "username", None), chat_id)

    if update.message:  # only reply where replying makes sense
        await update.message.reply_html(
            rf"Hi {user.mention_html()}!",
            reply_markup=ForceReply(selective=True),
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id, _ = _extract_text(update)
    logger.info("Received /help in chat_id=%s", chat_id)
    if update.message:
        await update.message.reply_text("Help!")


async def echo_any(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo for both user/group messages AND channel posts (text or caption)."""
    chat_id, text = _extract_text(update)
    user = update.effective_user

    # Log safely even for channel posts
    logger.info("Incoming update: from=%s chat_id=%s text=%r",
                getattr(user, "username", None), chat_id, text)

    if not text:
        # Non-text update (photo without caption, stickers, joins, etc.)
        return

    msg = update.effective_message
    if msg:
        await msg.reply_text(text)


# Global error handler so crashes don’t kill the loop
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled exception while processing update=%r", update)


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Text in private/groups
    application.add_handler(
        MessageHandler(
            (filters.ChatType.PRIVATE | filters.ChatType.GROUPS) & filters.TEXT & ~filters.COMMAND,
            echo_any,
        )
    )

    # Channel posts (text or media with caption)
    application.add_handler(
        MessageHandler(
            filters.ChatType.CHANNEL & (filters.TEXT | filters.CAPTION),
            echo_any,
        )
    )

    # Catch-all error logger
    application.add_error_handler(error_handler)

    # If you only care about messages & channel posts, you can reduce noise:
    application.run_polling(allowed_updates=[
        "message", "edited_message", "channel_post", "edited_channel_post"
    ])


if __name__ == "__main__":
    main()
