import io
from app import app
import database

def test_portal():
    client = app.test_client()
    
    # 1. Ana sayfa testi
    res = client.get("/")
    assert res.status_code == 200, f"Status: {res.status_code}"
    print("✓ Ana sayfa GET başarılı.")

    # 2. Fotoğraflar API testi
    res = client.get("/api/photos")
    assert res.status_code == 200
    data = res.get_json()
    assert "photos" in data
    print(f"✓ Fotoğraf listesi API başarılı ({len(data['photos'])} fotoğraf listelendi).")

    # 3. İstatistikler API testi
    res = client.get("/api/stats")
    assert res.status_code == 200
    stats = res.get_json()
    print(f"✓ İstatistikler: {stats}")

    # 4. Beğeni testi
    first_photo_id = data["photos"][0]["id"]
    res = client.post(f"/api/photos/{first_photo_id}/like")
    assert res.status_code == 200
    like_data = res.get_json()
    assert like_data["success"] is True
    print(f"✓ Beğeni testi başarılı (Yeni beğeni sayısı: {like_data['likes_count']}).")

    # 5. Kullanıcı fotoğraf yükleme testi (İSİM VE BAŞLIK GİRMEDEN, DOĞRUDAN ONAYSIZ YAYINLANMA)
    from PIL import Image
    test_img = Image.new("RGB", (200, 200), color=(200, 50, 50))
    img_data = io.BytesIO()
    test_img.save(img_data, format="PNG")
    img_data.seek(0)

    # Hiçbir isim veya başlık alanı göndermeden SADECE görsel yüklüyoruz
    user_upload_res = client.post("/api/upload", data={
        "photo": (img_data, "test_user_photo.png")
    }, content_type="multipart/form-data")
    assert user_upload_res.status_code == 200, f"Error: {user_upload_res.data}"
    user_upload_data = user_upload_res.get_json()
    assert user_upload_data["success"] is True
    assert user_upload_data["status"] == "approved"
    assert user_upload_data["photo"]["uploader_name"] == "Misafir"
    assert user_upload_data["photo"]["title"] == "Fotoğraf"
    print("✓ İsimsiz ve başlıksız kullanıcı yükleme testi başarılı: Doğrudan 'approved' olarak yayınlandı!")

    # 6. Yüklenen fotoğrafın anında ana akışta listelendiğini doğrulama
    res_after = client.get("/api/photos")
    all_photos = res_after.get_json()["photos"]
    user_photo_found = any(p["id"] == user_upload_data["photo"]["id"] for p in all_photos)
    assert user_photo_found is True
    print("✓ Kullanıcının yüklediği fotoğraf onay beklemeden anında ana akışta görüntülendi!")

    # 7. Gizli admin anahtarı ile giriş
    admin_key = database.get_admin_key()
    res_admin = client.get(f"/?admin_key={admin_key}")
    assert res_admin.status_code == 200
    print("✓ Gizli anahtar ile yönetici girişi başarılı.")

    # 11. Yönetici doğrudan fotoğraf yükleme testi
    admin_pil = Image.new("RGB", (300, 300), color=(50, 150, 250))
    admin_img = io.BytesIO()
    admin_pil.save(admin_img, format="PNG")
    admin_img.seek(0)
    admin_upload_res = client.post("/api/upload", data={
        "photo": (admin_img, "admin_masterpiece.png"),
        "title": "Yönetici Özel Çekimi",
        "description": "Benim kadrajımdan",
        "category": "Özel Seri"
    }, content_type="multipart/form-data")
    assert admin_upload_res.status_code == 200
    admin_upload_data = admin_upload_res.get_json()
    assert admin_upload_data["status"] == "approved"
    assert admin_upload_data["photo"]["uploader_role"] == "admin"
    # 12. Canlı sohbet mesaj gönderme ve alma testi
    chat_send_res = client.post("/api/chat/send", json={
        "message": "Merhaba, bu harika bir fotoğraf!",
        "sender_name": "Canan Z.",
        "session_id": "test_sess_1"
    })
    assert chat_send_res.status_code == 200
    chat_send_data = chat_send_res.get_json()
    assert chat_send_data["success"] is True
    print("✓ Canlı sohbet mesaj gönderme testi başarılı.")

    # 13. Mesajları sorgulama ve online sayısı testi
    chat_get_res = client.get("/api/chat/messages?session_id=test_sess_1")
    assert chat_get_res.status_code == 200
    chat_get_data = chat_get_res.get_json()
    assert len(chat_get_data["messages"]) >= 1
    assert chat_get_data["online_count"] >= 1
    print(f"✓ Canlı sohbet mesaj listesi ve çevrimiçi kullanıcı ({chat_get_data['online_count']}) testi başarılı.")

    print("\n🎉 TÜM TESTLER BAŞARIYLA GEÇTİ!")

if __name__ == "__main__":
    test_portal()
