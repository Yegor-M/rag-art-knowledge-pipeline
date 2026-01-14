# daily_art/config.py
from __future__ import annotations

import os
import re
import json
import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# ---- ENV / LOGGING ----

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("daily_art")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print(BASE_DIR)
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in environment / .env")

SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
if not BOT_TOKEN:
    raise RuntimeError("Set TELEGRAM_BOT_TOKEN in env")
if not CHAT_ID:
    raise RuntimeError("Set TELEGRAM_CHAT_ID (a user ID or @your_channel) in env")

DRAFTS_DIR = BASE_DIR / "drafts"
MESSAGES_DIR = BASE_DIR / "messages"

for d in (DRAFTS_DIR, MESSAGES_DIR):
    d.mkdir(parents=True, exist_ok=True)


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "_", text).strip("_")
    return text or "artwork"


# ---- JSON helpers ----

def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
