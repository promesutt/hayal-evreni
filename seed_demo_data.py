import os
import io
import math
from PIL import Image, ImageDraw, ImageFont
import database
from config import UPLOAD_FOLDER, THUMB_FOLDER

def generate_gradient_art(title, subtitle, color_start, color_end, width=1600, height=1200):
    """Yüksek kaliteli sanatsal bir demo görsel üretir"""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # Dikey/diyagonal renk geçişi (gradient)
    r1, g1, b1 = color_start
    r2, g2, b2 = color_end

    for y in range(height):
        factor = y / height
        # Hafif dalgalı sinüs dokusu
        wave = math.sin(y / 40.0) * 8
        r = int(max(0, min(255, r1 + (r2 - r1) * factor + wave)))
        g = int(max(0, min(255, g1 + (g2 - g1) * factor + wave)))
        b = int(max(0, min(255, b1 + (b2 - b1) * factor + wave)))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Dekoratif kamera vizör çizgileri ve daireler
    cx, cy = width // 2, height // 2
    draw.ellipse([cx - 260, cy - 260, cx + 260, cy + 260], outline=(255, 255, 255, 120), width=4)
    draw.ellipse([cx - 180, cy - 180, cx + 180, cy + 180], outline=(255, 255, 255, 80), width=2)
    draw.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], outline=(255, 255, 255, 140), width=3)
    
    # Vizör köşeleri
    corner_len = 50
    corners = [
        (80, 80, 80 + corner_len, 80, 80, 80 + corner_len),
        (width - 80, 80, width - 80 - corner_len, 80, width - 80, 80 + corner_len),
        (80, height - 80, 80 + corner_len, height - 80, 80, height - 80 - corner_len),
        (width - 80, height - 80, width - 80 - corner_len, height - 80, width - 80, height - 80 - corner_len),
    ]
    for x1, y1, x2, y2, x3, y3 in corners:
        draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, 200), width=4)
        draw.line([(x1, y1), (x3, y3)], fill=(255, 255, 255, 200), width=4)

    # Başlık metinleri
    draw.text((width // 2, height // 2 + 320), title, fill=(255, 255, 255), anchor="mm")
    draw.text((width // 2, height // 2 + 370), subtitle, fill=(230, 230, 230), anchor="mm")

    return img

def create_demo_photos():
    database.init_db()
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    THUMB_FOLDER.mkdir(parents=True, exist_ok=True)

    # Önceden yüklenmiş fotoğraf varsa tekrar ekleme
    existing = database.get_photos()
    if existing:
        print("Galeride zaten fotoğraflar mevcut, demo veriler atlandı.")
        return

    demos = [
        {
            "title": "Kızılçam Dağlarında Sis",
            "subtitle": "Kişisel Seçki • 50mm f/1.8",
            "category": "Doğa",
            "uploader_name": "Yönetici",
            "uploader_role": "admin",
            "status": "approved",
            "desc": "Sabahın ilk ışıklarında zirveden süzülen yoğun sis ve çam ormanının dinginliği.",
            "color1": (24, 48, 89),
            "color2": (14, 116, 144),
            "width": 1600,
            "height": 1100
        },
        {
            "title": "Eski Sokakların Gölgesi",
            "subtitle": "Kişisel Seçki • 35mm f/2.0",
            "category": "Sokak",
            "uploader_name": "Yönetici",
            "uploader_role": "admin",
            "status": "approved",
            "desc": "Tarihi taş sokaklarda öğle güneşinin oluşturduğu sert kontrast ve geometrik gölgeler.",
            "color1": (120, 53, 15),
            "color2": (217, 119, 6),
            "width": 1400,
            "height": 1600
        },
        {
            "title": "Metropolün Gece Işıkları",
            "subtitle": "Kişisel Seçki • 24mm f/2.8",
            "category": "Mimari",
            "uploader_name": "Yönetici",
            "uploader_role": "admin",
            "status": "approved",
            "desc": "Uzun pozlama tekniği ile yakalanan şehir trafiği ve gökdelenlerin neon yansımaları.",
            "color1": (88, 28, 135),
            "color2": (67, 56, 202),
            "width": 1600,
            "height": 1200
        },
        {
            "title": "Ege Kıyılarında Gün Batımı",
            "subtitle": "Topluluk Paylaşımı • Canan D.",
            "category": "Manzara",
            "uploader_name": "Canan D.",
            "uploader_role": "user",
            "status": "approved",
            "desc": "Ayvalık sahilinde dalgaların sakinleştiği altın saatlerde çekildi.",
            "color1": (194, 65, 12),
            "color2": (234, 88, 12),
            "width": 1500,
            "height": 1200
        },
        {
            "title": "Antik Tiyatroda Sessizlik",
            "subtitle": "Topluluk Paylaşımı • Murat S.",
            "category": "Mimari",
            "uploader_name": "Murat S.",
            "uploader_role": "user",
            "status": "approved",
            "desc": "Side antik tiyatrosunda zamana direnen mermer sütunlar.",
            "color1": (30, 41, 59),
            "color2": (71, 85, 105),
            "width": 1400,
            "height": 1500
        }
    ]

    for idx, item in enumerate(demos, 1):
        filename = f"demo_{idx}.webp"
        thumbname = f"thumb_demo_{idx}.webp"

        img = generate_gradient_art(
            item["title"],
            item["subtitle"],
            item["color1"],
            item["color2"],
            item["width"],
            item["height"]
        )

        # Ana görseli kaydet
        img.save(UPLOAD_FOLDER / filename, format="WEBP", quality=88)

        # Küçük resmi kaydet
        thumb = img.copy()
        thumb.thumbnail((750, 750), Image.Resampling.LANCZOS)
        thumb.save(THUMB_FOLDER / thumbname, format="WEBP", quality=82)

        # Veritabanına ekle
        photo_id = database.add_photo(
            filename=filename,
            original_filename=f"{item['title']}.webp",
            thumbnail=thumbname,
            title=item["title"],
            description=item["desc"],
            category=item["category"],
            uploader_name=item["uploader_name"],
            uploader_role=item["uploader_role"],
            status=item["status"]
        )
        # Birkaç demo beğeni ver
        for _ in range(idx * 3):
            database.like_photo(photo_id)

    print("Demo fotoğraflar başarıyla oluşturuldu!")

if __name__ == "__main__":
    create_demo_photos()
