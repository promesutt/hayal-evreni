import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
THUMB_FOLDER = BASE_DIR / "static" / "thumbs"
DB_PATH = BASE_DIR / "portal.db"

# Admin gizli anahtarı - Render Ortam Değişkeni (ADMIN_KEY) üzerinden okunur
DEFAULT_ADMIN_KEY = os.environ.get("ADMIN_KEY", "")
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "foto-portal-super-secret-key-3.1415")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif", "avif"}
MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB max per upload

# Telegram Bildirim Ayarları (Render Ortam Değişkeni / Environment Variable üzerinden okunur)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
