import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
    BANNED_PHRASES = os.getenv("BANNED_PHRASES", "").split("|")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")