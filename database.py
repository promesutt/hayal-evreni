import sqlite3
import time
from datetime import datetime
from config import DB_PATH, DEFAULT_ADMIN_KEY

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Fotoğraflar tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT,
            thumbnail TEXT NOT NULL,
            title TEXT,
            description TEXT,
            category TEXT DEFAULT 'Genel',
            uploader_name TEXT NOT NULL,
            uploader_role TEXT NOT NULL CHECK(uploader_role IN ('admin', 'user')),
            status TEXT NOT NULL CHECK(status IN ('approved', 'pending', 'rejected')),
            likes_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Sohbet mesajları tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_name TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Çevrimiçi kullanıcı oturumları tablosu (o an sayfada olanlar)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS online_users (
            session_id TEXT PRIMARY KEY,
            username TEXT,
            last_active REAL NOT NULL
        )
    """)

    # Ayarlar tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Varsayılan site ayarları
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_key', ?)", (DEFAULT_ADMIN_KEY,))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('site_title', 'Hayal Evreni')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('site_subtitle', 'özür dilerim')")
    
    # Mevcut ayarları güncelle
    cursor.execute("UPDATE settings SET value = 'Hayal Evreni' WHERE key = 'site_title'")
    cursor.execute("UPDATE settings SET value = 'özür dilerim' WHERE key = 'site_subtitle'")
    
    # Tüm bekleyen fotoğrafları doğrudan onaylı yap
    cursor.execute("UPDATE photos SET status = 'approved' WHERE status = 'pending'")
    
    conn.commit()
    conn.close()

def get_admin_key():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'admin_key'")
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else DEFAULT_ADMIN_KEY

def update_admin_key(new_key):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = 'admin_key'", (new_key,))
    conn.commit()
    conn.close()

def get_photos(search_query=None, sort_by="newest"):
    """Tüm onaylı fotoğrafları tek ve kesintisiz ana akışta getirir"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM photos WHERE status = 'approved'"
    params = []

    if search_query:
        query += " AND (title LIKE ? OR description LIKE ? OR uploader_name LIKE ?)"
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard])

    if sort_by == "likes":
        query += " ORDER BY likes_count DESC, id DESC"
    else:
        query += " ORDER BY id DESC"

    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_pending_photos():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM photos WHERE status = 'pending' ORDER BY id DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_photo_by_id(photo_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM photos WHERE id = ?", (photo_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_photo(filename, original_filename, thumbnail, title, description, category, uploader_name, uploader_role, status):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO photos (filename, original_filename, thumbnail, title, description, category, uploader_name, uploader_role, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (filename, original_filename, thumbnail, title, description, category, uploader_name, uploader_role, status))
    photo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return photo_id

def approve_photo(photo_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE photos SET status = 'approved' WHERE id = ?", (photo_id,))
    conn.commit()
    conn.close()

def reject_or_delete_photo(photo_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT filename, thumbnail FROM photos WHERE id = ?", (photo_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
        conn.commit()
    conn.close()
    return dict(row) if row else None

def like_photo(photo_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE photos SET likes_count = likes_count + 1 WHERE id = ?", (photo_id,))
    cursor.execute("SELECT likes_count FROM photos WHERE id = ?", (photo_id,))
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return row["likes_count"] if row else 0

def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM photos WHERE status = 'approved'")
    total_approved = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) as admin_count FROM photos WHERE status = 'approved' AND uploader_role = 'admin'")
    admin_count = cursor.fetchone()["admin_count"]
    cursor.execute("SELECT COUNT(*) as user_count FROM photos WHERE status = 'approved' AND uploader_role = 'user'")
    user_count = cursor.fetchone()["user_count"]
    cursor.execute("SELECT COUNT(*) as pending_count FROM photos WHERE status = 'pending'")
    pending_count = cursor.fetchone()["pending_count"]
    conn.close()
    return {
        "total_approved": total_approved,
        "admin_count": admin_count,
        "user_count": user_count,
        "pending_count": pending_count
    }

# ==================== SOHBET / CANLI CHAT FONKSİYONLARI ====================

def add_chat_message(sender_name, is_admin, message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_messages (sender_name, is_admin, message)
        VALUES (?, ?, ?)
    """, (sender_name, 1 if is_admin else 0, message))
    msg_id = cursor.lastrowid
    conn.commit()
    
    cursor.execute("SELECT * FROM chat_messages WHERE id = ?", (msg_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_chat_messages(after_id=0, limit=60):
    conn = get_db()
    cursor = conn.cursor()
    if after_id > 0:
        cursor.execute("""
            SELECT * FROM chat_messages 
            WHERE id > ? 
            ORDER BY id ASC 
            LIMIT ?
        """, (after_id, limit))
    else:
        # İlk yüklemede son mesajları getir
        cursor.execute("""
            SELECT * FROM (
                SELECT * FROM chat_messages ORDER BY id DESC LIMIT ?
            ) ORDER BY id ASC
        """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def update_online_user(session_id, username=None):
    """Kullanıcının aktif olduğunu işaretler ve eski (15 saniyeden eski) oturumları temizler"""
    now = time.time()
    conn = get_db()
    cursor = conn.cursor()
    
    # 15 saniyeden eski çevrimdışı kullanıcıları temizle
    cursor.execute("DELETE FROM online_users WHERE last_active < ?", (now - 20,))
    
    # Bu oturumu ekle / güncelle
    cursor.execute("""
        INSERT INTO online_users (session_id, username, last_active)
        VALUES (?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET 
            last_active = excluded.last_active,
            username = coalesce(excluded.username, online_users.username)
    """, (session_id, username, now))
    
    # Güncel çevrimiçi kullanıcı sayısını al (en az 1)
    cursor.execute("SELECT COUNT(*) as count FROM online_users")
    count = cursor.fetchone()["count"]
    
    conn.commit()
    conn.close()
    return max(1, count)

def delete_chat_message(message_id):
    """Yönetici için sohbet mesajını siler"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages WHERE id = ?", (message_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_recent_message_ids(limit=80):
    """Aktif mesaj ID'lerini döndürür (silinenleri tespit etmek için)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM chat_messages ORDER BY id DESC LIMIT ?", (limit,))
    ids = [row["id"] for row in cursor.fetchall()]
    conn.close()
    return ids

def get_online_count():
    now = time.time()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM online_users WHERE last_active < ?", (now - 20,))
    cursor.execute("SELECT COUNT(*) as count FROM online_users")
    count = cursor.fetchone()["count"]
    conn.commit()
    conn.close()
    return max(1, count)
