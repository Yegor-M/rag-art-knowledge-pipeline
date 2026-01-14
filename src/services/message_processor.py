from dataclasses import dataclass
from typing import Optional
from telegram import Message

@dataclass
class ProcessedMessage:
    action: str  # "APPROVE"|"DELETE"|"REPLY"
    response: Optional[str]

class MessageProcessor:
    def __init__(self, rules: dict):
        self.rules = rules  # Load from config
        
    async def process_incoming(self, message: Message) -> ProcessedMessage:
        text = message.text.lower()
        
        if any(banned in text for banned in self.rules["banned_phrases"]):
            return ProcessedMessage("DELETE", None)
            
        if "urgent" in text:
            return ProcessedMessage("REPLY", "⚠️ Message flagged for review")
            
        return ProcessedMessage("APPROVE", None)