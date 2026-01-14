import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    filters
)
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /hello command"""
    try:
        await update.message.reply_text(f'Hello {update.effective_user.first_name}!')
        logger.info(f"Replied to user {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error in hello handler: {e}", exc_info=True)

async def post_init(application):
    """Runs after bot initialization"""
    await application.bot.set_my_commands([
        ('hello', 'Say hello to the bot'),
    ])
    logger.info("Bot commands set up")

def main():
    try:
        token = os.getenv("TELEGRAM_TOKEN")z
        application = ApplicationBuilder() \
            .token(token) \
            .post_init(post_init) \
            .build()

        # Add handlers
        application.add_handler(CommandHandler("hello", hello, filters=filters.ChatType.PRIVATE))

        # Start the bot
        logger.info("Starting bot...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            close_loop=False  # Important for proper shutdown
        )
    except Exception as e:
        logger.critical(f"Bot crashed: {e}", exc_info=True)
    finally:
        logger.info("Bot stopped")

if __name__ == "__main__":
    # Proper event loop handling
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)