import os
import uuid
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename
from config import UPLOAD_FOLDER, THUMB_FOLDER, ALLOWED_EXTENSIONS

def is_allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def process_and_save_image(file_storage):
    """
    Kullanıcının yüklediği görseli işler:
    - EXIF yönlendirmesini düzeltir
    - Büyük görselleri optimize eder (max 2560px)
    - Hızlı yükleme için küçük resim (thumbnail - max 700px) üretir
    - Güvenli rastgele bir dosya adı oluşturur
    """
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    THUMB_FOLDER.mkdir(parents=True, exist_ok=True)

    original_filename = secure_filename(file_storage.filename) or "foto.jpg"
    ext = original_filename.rsplit(".", 1)[1].lower() if "." in original_filename else "jpg"
    if ext not in ALLOWED_EXTENSIONS:
        ext = "jpg"

    unique_id = uuid.uuid4().hex
    target_filename = f"{unique_id}.webp"
    thumb_filename = f"thumb_{unique_id}.webp"

    target_path = UPLOAD_FOLDER / target_filename
    thumb_path = THUMB_FOLDER / thumb_filename

    # Pillow ile aç
    image = Image.open(file_storage.stream)

    # EXIF yönlendirmesini uygula (akıllı telefon fotoğrafları için kritik)
    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    # RGB formatına dönüştür (PNG veya RGBA durumunda WebP şeffaflığı korur, CMYK ise RGB'ye çevir)
    if image.mode in ("CMYK", "P"):
        image = image.convert("RGB")
    elif image.mode == "RGBA":
        # PNG şeffaflık
        pass
    else:
        image = image.convert("RGB")

    # 1. Ana Görsel Optimizasyonu (Maksimum 2560px)
    max_main_dimension = 2560
    main_img = image.copy()
    if max(main_img.size) > max_main_dimension:
        main_img.thumbnail((max_main_dimension, max_main_dimension), Image.Resampling.LANCZOS)
    
    main_img.save(target_path, format="WEBP", quality=88, method=4)

    # 2. Hızlı Küçük Resim / Thumbnail (Maksimum 750px genişlik/yükseklik)
    thumb_img = image.copy()
    thumb_img.thumbnail((750, 750), Image.Resampling.LANCZOS)
    thumb_img.save(thumb_path, format="WEBP", quality=82, method=4)

    return target_filename, thumb_filename, original_filename

def remove_image_files(filename, thumb_filename):
    """Silinen fotoğrafın diskteki dosyalarını temizler"""
    try:
        main_path = UPLOAD_FOLDER / filename
        if main_path.exists():
            main_path.unlink()
    except Exception as e:
        print(f"Dosya silme hatası ({filename}): {e}")

    try:
        thumb_path = THUMB_FOLDER / thumb_filename
        if thumb_path.exists():
            thumb_path.unlink()
    except Exception as e:
        print(f"Thumbnail silme hatası ({thumb_filename}): {e}")
