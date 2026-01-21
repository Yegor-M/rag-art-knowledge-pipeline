from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from daily_art.connectors.http_client import SESSION


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str
    chat_id: str


class TelegramClient:
    def __init__(self, cfg: TelegramConfig):
        self.cfg = cfg

    def send_photo(
        self,
        *,
        photo_url: str,
        caption: str,
        caption_entities: List[Dict[str, Any]],
        timeout: int = 20,
    ) -> Dict[str, Any]:
        if not self.cfg.bot_token:
            raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")
        if not self.cfg.chat_id:
            raise RuntimeError("Missing TELEGRAM_CHAT_ID")

        url = f"https://api.telegram.org/bot{self.cfg.bot_token}/sendPhoto"
        payload = {
            "chat_id": self.cfg.chat_id,
            "photo": photo_url,
            "caption": caption,
            "caption_entities": json.dumps(caption_entities, ensure_ascii=False),
        }
        r = SESSION.post(url, data=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()
