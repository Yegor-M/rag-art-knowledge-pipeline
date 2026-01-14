import logging
from typing import Optional, List
from telegram import Bot, Update, Message, Chat
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters
)

logger = logging.getLogger(__name__)

class TelegramClient:
    def __init__(self, token: str):
        self.bot = Bot(token)
        self.app = ApplicationBuilder().token(token).build()
        
    async def post_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: Optional[str] = "HTML",
        reply_to: Optional[int] = None
    ) -> Message:
        return await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_to_message_id=reply_to
        )
    
    async def delete_message(self, chat_id: str, message_id: int) -> bool:
        return await self.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id
        )
    
    def register_handler(self, handler):
        """Decorator to register command handlers"""
        self.app.add_handler(handler)