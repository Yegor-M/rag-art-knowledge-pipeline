from telegram import Bot, Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext
)
from src.services.message_processor import MessageProcessor

async def admin_filter(update: Update) -> bool:
    """Check if user is admin"""
    user = update.effective_user
    chat = update.effective_chat
    admins = await chat.get_administrators()
    return user.id in [admin.user.id for admin in admins]

class ChannelHandlers:
    def __init__(self, processor: MessageProcessor):
        self.processor = processor
    
    async def handle_new_message(self, update: Update, context: CallbackContext):
        if not await admin_filter(update):
            return
            
        message = update.effective_message
        processed = await self.processor.process_incoming(message)
        
        if processed.action == "DELETE":
            await message.delete()
        elif processed.action == "REPLY":
            await message.reply_text(processed.response)

    def get_handlers(self) -> list:
        return [
            MessageHandler(
                filters.ChatType.CHANNEL & filters.TEXT,
                self.handle_new_message
            )
        ]