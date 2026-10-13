import os
import sqlite3
import time
from datetime import datetime
from config import DB_PATH, DEFAULT_ADMIN_KEY

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def is_postgres():
    return bool(DATABASE_URL)

def get_db():
    if is_postgres():
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def q(sql):
    """Sorgudaki parametre işaretlerini veritabanı türüne göre dönüştürür (? -> %s)"""
    if is_postgres():
        return sql.replace("?", "%s")
    return sql

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    id_type = "SERIAL PRIMARY KEY" if is_postgres() else "INTEGER PRIMARY KEY AUTOINCREMENT"
    real_type = "DOUBLE PRECISION" if is_postgres() else "REAL"

    # Fotoğraflar tablosu
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS photos (
            id {id_type},
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
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id {id_type},
            sender_name TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Çevrimiçi kullanıcılar
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS online_users (
            session_id TEXT PRIMARY KEY,
            username TEXT,
            last_active {real_type} NOT NULL
        )
    """)

    # Ayarlar
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Varsayılan ayarlar
    if is_postgres():
        cursor.execute("""
            INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING
        """, ('admin_key', DEFAULT_ADMIN_KEY))
        cursor.execute("""
            INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING
        """, ('site_title', 'Hayal Evreni'))
        cursor.execute("""
            INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING
        """, ('site_subtitle', 'özür dilerim'))
    else:
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_key', ?)", (DEFAULT_ADMIN_KEY,))
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('site_title', 'Hayal Evreni')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('site_subtitle', 'özür dilerim')")

    cursor.execute(q("UPDATE settings SET value = 'Hayal Evreni' WHERE key = 'site_title'"))
    cursor.execute(q("UPDATE settings SET value = 'özür dilerim' WHERE key = 'site_subtitle'"))
    cursor.execute(q("UPDATE photos SET status = 'approved' WHERE status = 'pending'"))

    conn.commit()
    conn.close()

def get_admin_key():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(q("SELECT value FROM settings WHERE key = ?"), ('admin_key',))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else DEFAULT_ADMIN_KEY

def update_admin_key(new_key):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(q("UPDATE settings SET value = ? WHERE key = 'admin_key'"), (new_key,))
    conn.commit()
    conn.close()

def get_photos(search_query=None, sort_by="newest"):
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

    cursor.execute(q(query), params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_pending_photos():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(q("SELECT * FROM photos WHERE status = 'pending' ORDER BY id DESC"))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_photo_by_id(photo_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(q("SELECT * FROM photos WHERE id = ?"), (photo_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_photo(filename, original_filename, thumbnail, title, description, category, uploader_name, uploader_role, status):
    conn = get_db()
    cursor = conn.cursor()
    
    if is_postgres():
        cursor.execute("""
            INSERT INTO photos (filename, original_filename, thumbnail, title, description, category, uploader_name, uploader_role, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (filename, original_filename, thumbnail, title, description, category, uploader_name, uploader_role, status))
        photo_id = cursor.fetchone()["id"]
    else:
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
    cursor.execute(q("UPDATE photos SET status = 'approved' WHERE id = ?"), (photo_id,))
    conn.commit()
    conn.close()

def reject_or_delete_photo(photo_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(q("SELECT filename, thumbnail FROM photos WHERE id = ?"), (photo_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute(q("DELETE FROM photos WHERE id = ?"), (photo_id,))
        conn.commit()
    conn.close()
    return dict(row) if row else None

def like_photo(photo_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(q("UPDATE photos SET likes_count = likes_count + 1 WHERE id = ?"), (photo_id,))
    cursor.execute(q("SELECT likes_count FROM photos WHERE id = ?"), (photo_id,))
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return row["likes_count"] if row else 0

def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM photos WHERE status = 'approved'")
    total_approved = cursor.fetchone()["total"]
    cursor.execute(q("SELECT COUNT(*) as admin_count FROM photos WHERE status = 'approved' AND uploader_role = ?"), ('admin',))
    admin_count = cursor.fetchone()["admin_count"]
    cursor.execute(q("SELECT COUNT(*) as user_count FROM photos WHERE status = 'approved' AND uploader_role = ?"), ('user',))
    user_count = cursor.fetchone()["user_count"]
    cursor.execute(q("SELECT COUNT(*) as pending_count FROM photos WHERE status = ?"), ('pending',))
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
    
    if is_postgres():
        cursor.execute("""
            INSERT INTO chat_messages (sender_name, is_admin, message)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (sender_name, 1 if is_admin else 0, message))
        msg_id = cursor.fetchone()["id"]
    else:
        cursor.execute("""
            INSERT INTO chat_messages (sender_name, is_admin, message)
            VALUES (?, ?, ?)
        """, (sender_name, 1 if is_admin else 0, message))
        msg_id = cursor.lastrowid

    conn.commit()
    
    cursor.execute(q("SELECT * FROM chat_messages WHERE id = ?"), (msg_id,))
    row = cursor.fetchone()
    conn.close()
    
    # created_at datetime objesi gelebilir, string formatına dönüştürelim
    if row:
        row_dict = dict(row)
        if isinstance(row_dict.get("created_at"), datetime):
            row_dict["created_at"] = row_dict["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        return row_dict
    return None

def get_chat_messages(after_id=0, limit=60):
    conn = get_db()
    cursor = conn.cursor()
    if after_id > 0:
        cursor.execute(q("""
            SELECT * FROM chat_messages 
            WHERE id > ? 
            ORDER BY id ASC 
            LIMIT ?
        """), (after_id, limit))
    else:
        cursor.execute(q("""
            SELECT * FROM (
                SELECT * FROM chat_messages ORDER BY id DESC LIMIT ?
            ) sub ORDER BY id ASC
        """), (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # created_at alanlarını string formatına garantiye al
    for r in rows:
        if isinstance(r.get("created_at"), datetime):
            r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            
    return rows

def update_online_user(session_id, username=None):
    now = time.time()
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(q("DELETE FROM online_users WHERE last_active < ?"), (now - 20,))
    
    cursor.execute(q("""
        INSERT INTO online_users (session_id, username, last_active)
        VALUES (?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET 
            last_active = EXCLUDED.last_active,
            username = coalesce(EXCLUDED.username, online_users.username)
    """), (session_id, username, now))
    
    cursor.execute("SELECT COUNT(*) as count FROM online_users")
    count = cursor.fetchone()["count"]
    
    conn.commit()
    conn.close()
    return max(1, count)

def delete_chat_message(message_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(q("DELETE FROM chat_messages WHERE id = ?"), (message_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_recent_message_ids(limit=80):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(q("SELECT id FROM chat_messages ORDER BY id DESC LIMIT ?"), (limit,))
    ids = [row["id"] for row in cursor.fetchall()]
    conn.close()
    return ids

def get_online_count():
    now = time.time()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(q("DELETE FROM online_users WHERE last_active < ?"), (now - 20,))
    cursor.execute("SELECT COUNT(*) as count FROM online_users")
    count = cursor.fetchone()["count"]
    conn.commit()
    conn.close()
    return max(1, count)
