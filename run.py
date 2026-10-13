import os
import sys
import webbrowser
import threading
import time
from pathlib import Path

# Sanal ortamı otomatik kontrol et veya mevcut python ile çalıştır
BASE_DIR = Path(__file__).resolve().parent

import database
import seed_demo_data
from app import app

def open_browser():
    time.sleep(1.2)
    # Yönetici bağlantısıyla tarayıcıyı aç
    admin_url = "http://127.0.0.1:5001/?admin_key=foto-admin-2026"
    print(f"\n🚀 Tarayıcı açılıyor: {admin_url}")
    try:
        webbrowser.open(admin_url)
    except Exception:
        pass

if __name__ == "__main__":
    database.init_db()
    seed_demo_data.create_demo_photos()
    
    admin_key = database.get_admin_key()
    
    print("\n" + "="*65)
    print(" 🌌 HAYAL EVRENİ | 'özür dilerim'")
    print("="*65)
    print(" 🌐 Ziyaretçi Görünümü:")
    print("    http://127.0.0.1:5001/")
    print("\n 👑 Size Özel Yönetici (Admin) Bağlantısı:")
    print(f"    http://127.0.0.1:5001/?admin_key={admin_key}")
    print("\n 📌 Bu bağlantı ile girdiğinizde:")
    print("    - Doğrudan 'Yönetici Seçkisi' fotoğrafları yükleyebilirsiniz.")
    print("    - Ziyaretçilerin gönderdiği fotoğrafları onaylayabilir / silebilirsiniz.")
    print("    - Şifre yazmanıza gerek kalmaz, bu link yönetici oturumunu açar.")
    print("="*65 + "\n")

    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=5001, debug=False)
