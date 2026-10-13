import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
THUMB_FOLDER = BASE_DIR / "static" / "thumbs"
DB_PATH = BASE_DIR / "portal.db"

# Admin gizli anahtarı - tarayıcıda '?admin_key=foto-admin-2026' ile doğrudan giriş yapılır
DEFAULT_ADMIN_KEY = "foto-admin-2026"
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "foto-portal-super-secret-key-3.1415")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif", "avif"}
MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB max per upload
