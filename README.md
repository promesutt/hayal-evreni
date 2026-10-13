# 🌌 Hayal Evreni - *özür dilerim*

Fotoğraf akışı ve anlık canlı sohbet alanı. Herkesin doğrudan fotoğraf yükleyebildiği ve birbirleriyle konuşabildiği sade görsel portal.

---

## 🚀 Hızlı Başlangıç (Nasıl Çalıştırılır?)

Terminalde:

```bash
./start.sh
```

Veya sanal ortam ile:

```bash
source .venv/bin/activate
python run.py
```

---

## 🔗 Giriş Linkleri

| Rol | URL | Açıklama |
| :--- | :--- | :--- |
| **Normal Ziyaretçi Görünümü** | `http://127.0.0.1:5001/` | Fotoğraf akışını inceler, beğenir, **"+ Fotoğraf Paylaş"** ile görsel ekler ve sağ alttaki **Canlı Sohbet** penceresinden yazışabilir. |
| **Size Özel Yönetici Linki** | `http://127.0.0.1:5001/?admin_key=foto-admin-2026` | **Şifresiz doğrudan yönetim yetkisi.** Doğrudan fotoğraf yükleme, Onay Havuzu ve silme butonları aktiftir. Sohbette mesajlarınız **👑 Yönetici** olarak görünür. |

---

## 🌟 Neler Değişti & Yeni Özellikler

1. **Karmaşıklık Kaldırıldı (Tek ve Akıcı Ana Akış):**
   - Karışık sekme ve filtreler kaldırıldı ("ordan gelenler burdan gelenler" yok).
   - Hem sizin fotoğraflarınız hem de onayladığınız kullanıcı fotoğrafları tek, kesintisiz ve şık bir akışta birlikte sergilenir.
   - Fotoğrafların üzerinde kimin paylaştığı (👑 Yönetici veya 👤 Ziyaretçi Adı) net şekilde görünür.

2. **💬 Anlık Canlı Sohbet Penceresi (Live Chat):**
   - Sayfanın sağ alt köşesinde açılıp kapanabilir zarif bir sohbet penceresi eklendi.
   - **Çevrimiçi Sayaç:** O an sayfada kaç kişinin aktif olduğunu gösterir (`🟢 2 kişi sayfada aktif`).
   - **Gerçek Zamanlı İletişim:** Sayfadaki herkes rumuzunu yazarak anında birbirleriyle sohbet edebilir.
   - **Yönetici Ayrımı:** Siz yazdığınızda mesajlarınız altın sarısı taç ve `👑 Yönetici` etiketiyle özel olarak vurgulanır.
   - **Okunmamış Mesaj Rozeti:** Sohbet kapalıyken yeni bir mesaj geldiğinde bildirim rozeti yanıp söner.

3. **Doğrudan Fotoğraf Paylaşımı (Onaysız & Şartsız):**
   - **Onay Zorunluluğu Kaldırıldı:** Artık yönetici onayı bekleme süreci tamamen kaldırıldı. Kullanıcılar veya siz fotoğraf yüklediğiniz anda doğrudan ana akışta yayınlanır.
   - **İsim, Başlık vs. Zorunlu Değil:** Tek zorunlu şey fotoğraf dosyasını seçmektir. İsim veya başlık girmeden tek tıkla fotoğraf yüklenebilir. İsim girilmezse otomatik olarak `Misafir`, başlık girilmezse `Fotoğraf` olarak listelenir.
   - **Yönetici Kontrolü:** İstemediğiniz veya uygunsuz bulduğunuz herhangi bir fotoğrafı yönetici linkinizle girip fotoğrafa tıklayarak tek tıkla (`Fotoğrafı Sil`) kaldırabilirsiniz.
