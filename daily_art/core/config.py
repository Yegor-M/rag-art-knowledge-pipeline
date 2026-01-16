from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    # Paths
    base_dir: Path
    data_dir: Path
    drafts_dir: Path
    messages_dir: Path
    kb_dir: Path

    # Logging
    log_level: str

    # API keys / credentials
    openai_api_key: str
    serper_api_key: str
    telegram_bot_token: str
    telegram_chat_id: str

    # Defaults
    openai_model: str = "gpt-4o-mini"


def load_settings() -> Settings:
    pkg_dir = Path(__file__).resolve().parents[1]   # daily_art/ package dir
    repo_dir = pkg_dir.parent                       # repo root

    env_path = repo_dir / ".env"
    load_dotenv(env_path)

    data_dir = repo_dir / "data"
    drafts_dir = data_dir / "drafts"
    messages_dir = data_dir / "messages"
    kb_dir = data_dir / "kb"

    return Settings(
        base_dir=repo_dir,
        data_dir=data_dir,
        drafts_dir=drafts_dir,
        messages_dir=messages_dir,
        kb_dir=kb_dir,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        serper_api_key=os.getenv("SERPER_API_KEY", "").strip(),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini",
    )
