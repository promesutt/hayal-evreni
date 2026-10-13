import os
import uuid
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config import SECRET_KEY, DEFAULT_ADMIN_KEY, MAX_CONTENT_LENGTH
import database
from image_utils import is_allowed_file, process_and_save_image, remove_image_files

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# Veritabanını ve başlangıç demo verilerini başlat
database.init_db()
try:
    import seed_demo_data
    seed_demo_data.create_demo_photos()
except Exception as e:
    pass

def check_is_admin():
    """Oturum veya istekteki admin anahtarını kontrol eder"""
    current_key = database.get_admin_key()
    
    # 1. Query parameter ile kontrol (örn: ?admin_key=...)
    param_key = request.args.get("admin_key") or request.args.get("token")
    if param_key and param_key == current_key:
        session["is_admin"] = True
        return True
        
    # 2. Header ile kontrol
    header_key = request.headers.get("X-Admin-Key")
    if header_key and header_key == current_key:
        return True
        
    # 3. Session ile kontrol
    return session.get("is_admin", False) is True

@app.route("/")
def index():
    admin_key_param = request.args.get("admin_key") or request.args.get("token")
    current_key = database.get_admin_key()
    
    if admin_key_param:
        if admin_key_param == current_key:
            session["is_admin"] = True
        else:
            session["is_admin"] = False
            
    is_admin = session.get("is_admin", False)
    admin_key = current_key if is_admin else None
    
    return render_template(
        "index.html",
        is_admin=is_admin,
        admin_key=admin_key
    )

@app.route("/admin")
def admin_entry():
    token = request.args.get("token") or request.args.get("admin_key")
    current_key = database.get_admin_key()
    
    if token and token == current_key:
        session["is_admin"] = True
        return redirect(url_for("index", admin_key=token))
        
    return redirect(url_for("index"))

@app.route("/api/admin/verify", methods=["POST"])
def verify_admin():
    data = request.get_json() or {}
    key = data.get("key", "").strip()
    current_key = database.get_admin_key()
    
    if key == current_key:
        session["is_admin"] = True
        return jsonify({"success": True, "message": "Yönetici girişi başarılı"})
    return jsonify({"success": False, "message": "Geçersiz yönetici anahtarı"}), 401

@app.route("/api/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("is_admin", None)
    return jsonify({"success": True, "message": "Çıkış yapıldı"})

# ==================== FOTOĞRAF API ROTLARI ====================

@app.route("/api/photos", methods=["GET"])
def list_photos():
    search_query = request.args.get("search", "").strip() or None
    sort_by = request.args.get("sort", "newest")
    
    # Tüm onaylı fotoğrafları tek ana akışta getir
    photos = database.get_photos(search_query=search_query, sort_by=sort_by)
    return jsonify({"photos": photos})

@app.route("/api/admin/pending", methods=["GET"])
def pending_photos():
    if not check_is_admin():
        return jsonify({"error": "Yetkisiz erişim"}), 403
    pending = database.get_pending_photos()
    return jsonify({"pending_photos": pending})

@app.route("/api/stats", methods=["GET"])
def get_stats():
    stats = database.get_stats()
    stats["is_admin"] = check_is_admin()
    stats["online_count"] = database.get_online_count()
    return jsonify(stats)

@app.route("/api/upload", methods=["POST"])
def upload_photo():
    if "photo" not in request.files:
        return jsonify({"success": False, "message": "Lütfen bir fotoğraf dosyası seçin."}), 400
        
    file = request.files["photo"]
    if file.filename == "":
        return jsonify({"success": False, "message": "Dosya seçilmedi."}), 400
        
    if not is_allowed_file(file.filename):
        return jsonify({"success": False, "message": "Desteklenmeyen dosya türü. (JPG, PNG, WEBP geçerlidir)"}), 400

    # İsim ve başlık zorunlu değil; boş bırakılırsa varsayılan değerler atanır
    title = request.form.get("title", "").strip() or "Fotoğraf"
    description = request.form.get("description", "").strip()
    category = "Genel"
    
    is_admin = check_is_admin()

    try:
        filename, thumb_filename, original_name = process_and_save_image(file)
    except Exception as e:
        return jsonify({"success": False, "message": f"Görsel işlenirken bir hata oluştu: {str(e)}"}), 500

    if is_admin:
        uploader_name = "👑 Yönetici"
        uploader_role = "admin"
    else:
        uploader_name = request.form.get("uploader_name", "").strip() or "Misafir"
        uploader_role = "user"

    # Yönetici onayı gerekmez, doğrudan 'approved' olarak kaydedilir ve akışta yayınlanır
    photo_id = database.add_photo(
        filename=filename,
        original_filename=original_name,
        thumbnail=thumb_filename,
        title=title,
        description=description,
        category=category,
        uploader_name=uploader_name,
        uploader_role=uploader_role,
        status="approved"
    )
    
    photo = database.get_photo_by_id(photo_id)
    return jsonify({
        "success": True,
        "status": "approved",
        "message": "Fotoğrafınız başarıyla yüklendi ve akışta yayınlandı!",
        "photo": photo
    })

@app.route("/api/admin/approve/<int:photo_id>", methods=["POST"])
def approve(photo_id):
    if not check_is_admin():
        return jsonify({"error": "Yetkisiz erişim"}), 403
        
    database.approve_photo(photo_id)
    return jsonify({"success": True, "message": "Fotoğraf onaylandı ve ana akışa eklendi!"})

@app.route("/api/admin/photo/<int:photo_id>", methods=["DELETE"])
def delete_photo(photo_id):
    if not check_is_admin():
        return jsonify({"error": "Yetkisiz erişim"}), 403
        
    deleted_row = database.reject_or_delete_photo(photo_id)
    if deleted_row:
        remove_image_files(deleted_row["filename"], deleted_row["thumbnail"])
        return jsonify({"success": True, "message": "Fotoğraf silindi."})
    return jsonify({"success": False, "message": "Fotoğraf bulunamadı."}), 404

@app.route("/api/photos/<int:photo_id>/like", methods=["POST"])
def like(photo_id):
    new_count = database.like_photo(photo_id)
    return jsonify({"success": True, "likes_count": new_count})

# ==================== CANLI SOHBET (CHAT) API ROTLARI ====================

@app.route("/api/chat/messages", methods=["GET"])
def get_messages():
    after_id = int(request.args.get("after", 0))
    session_id = request.args.get("session_id", "").strip()
    username = request.args.get("username", "").strip()
    
    online_count = 1
    if session_id:
        online_count = database.update_online_user(session_id, username)
    else:
        online_count = database.get_online_count()
        
    messages = database.get_chat_messages(after_id=after_id)
    return jsonify({
        "messages": messages,
        "online_count": online_count
    })

@app.route("/api/chat/send", methods=["POST"])
def send_message():
    data = request.get_json() or {}
    text = data.get("message", "").strip()
    sender_name = data.get("sender_name", "").strip() or "Misafir"
    session_id = data.get("session_id", "").strip()
    
    if not text:
        return jsonify({"success": False, "message": "Mesaj boş olamaz"}), 400

    is_admin = check_is_admin()
    if is_admin:
        sender_name = "👑 Yönetici"

    msg = database.add_chat_message(sender_name, is_admin, text)
    
    online_count = 1
    if session_id:
        online_count = database.update_online_user(session_id, sender_name)
    else:
        online_count = database.get_online_count()

    return jsonify({
        "success": True,
        "message": msg,
        "online_count": online_count
    })

@app.route("/api/chat/ping", methods=["POST"])
def ping_chat():
    data = request.get_json() or {}
    session_id = data.get("session_id", "").strip()
    username = data.get("username", "").strip()
    
    online_count = 1
    if session_id:
        online_count = database.update_online_user(session_id, username)
    else:
        online_count = database.get_online_count()
        
    return jsonify({"online_count": online_count})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
