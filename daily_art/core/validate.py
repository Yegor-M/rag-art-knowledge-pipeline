from __future__ import annotations
from dataclasses import dataclass
from typing import List
from .config import Settings


@dataclass(frozen=True)
class ValidationError(Exception):
    missing: List[str]

    def __str__(self) -> str:
        return "Missing required environment variables: " + ", ".join(self.missing)


def validate_settings(s: Settings, *, require_telegram: bool = True, require_serper: bool = False) -> None:
    missing: list[str] = []

    if not s.openai_api_key:
        missing.append("OPENAI_API_KEY")

    if require_serper and not s.serper_api_key:
        missing.append("SERPER_API_KEY")

    if require_telegram:
        if not s.telegram_bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not s.telegram_chat_id:
            missing.append("TELEGRAM_CHAT_ID")

    if missing:
        raise ValidationError(missing)
