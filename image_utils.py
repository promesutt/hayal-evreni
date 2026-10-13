import os
import uuid
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename
from config import UPLOAD_FOLDER, THUMB_FOLDER, ALLOWED_EXTENSIONS

try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.utils
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

def is_cloudinary_configured():
    if not CLOUDINARY_AVAILABLE:
        return False
    if os.environ.get("CLOUDINARY_URL"):
        return True
    return bool(
        os.environ.get("CLOUDINARY_CLOUD_NAME") and
        os.environ.get("CLOUDINARY_API_KEY") and
        os.environ.get("CLOUDINARY_API_SECRET")
    )

def init_cloudinary():
    if not is_cloudinary_configured():
        return
    if not os.environ.get("CLOUDINARY_URL"):
        cloudinary.config(
            cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
            api_key=os.environ.get("CLOUDINARY_API_KEY"),
            api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
            secure=True
        )

def is_allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def process_and_save_image(file_storage):
    """
    Kullanıcının yüklediği görseli işler:
    - Cloudinary ayarlıysa kalıcı olarak buluta yükler
    - Değilse yerel diske optimize WebP olarak kaydeder
    """
    original_filename = secure_filename(file_storage.filename) or "foto.jpg"
    
    # 1. Cloudinary bulut yüklemesi (Kalıcı ve silinmez)
    if is_cloudinary_configured():
        try:
            init_cloudinary()
            unique_id = uuid.uuid4().hex
            
            res = cloudinary.uploader.upload(
                file_storage.stream,
                public_id=f"hayal_{unique_id}",
                folder="hayal_evreni",
                transformation=[
                    {"width": 2560, "height": 2560, "crop": "limit", "quality": "auto", "fetch_format": "auto"}
                ]
            )
            main_url = res["secure_url"]
            # Hızlı yükleme için 750px kare kırpılmış thumbnail URL'i
            thumb_url = main_url.replace("/upload/", "/upload/c_fill,w_750,h_750,g_auto,q_auto,f_auto/")
            return main_url, thumb_url, original_filename
        except Exception as e:
            print(f"[Cloudinary Yükleme Hatası, yerel diske dönülüyor]: {e}")

    # 2. Yerel disk yüklemesi (Fallback)
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    THUMB_FOLDER.mkdir(parents=True, exist_ok=True)

    unique_id = uuid.uuid4().hex
    target_filename = f"{unique_id}.webp"
    thumb_filename = f"thumb_{unique_id}.webp"

    target_path = UPLOAD_FOLDER / target_filename
    thumb_path = THUMB_FOLDER / thumb_filename

    image = Image.open(file_storage.stream)

    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    if image.mode in ("CMYK", "P"):
        image = image.convert("RGB")
    elif image.mode != "RGBA":
        image = image.convert("RGB")

    max_main_dimension = 2560
    main_img = image.copy()
    if max(main_img.size) > max_main_dimension:
        main_img.thumbnail((max_main_dimension, max_main_dimension), Image.Resampling.LANCZOS)
    
    main_img.save(target_path, format="WEBP", quality=88, method=4)

    thumb_img = image.copy()
    thumb_img.thumbnail((750, 750), Image.Resampling.LANCZOS)
    thumb_img.save(thumb_path, format="WEBP", quality=82, method=4)

    return target_filename, thumb_filename, original_filename

def remove_image_files(filename, thumb_filename):
    """Silinen fotoğrafın dosyalarını temizler"""
    if filename.startswith("http") and is_cloudinary_configured():
        try:
            init_cloudinary()
            parts = filename.split("/")
            if "hayal_evreni" in parts:
                idx = parts.index("hayal_evreni")
                public_id = "/".join(parts[idx:]).rsplit(".", 1)[0]
                cloudinary.uploader.destroy(public_id)
        except Exception as e:
            print(f"Cloudinary silme hatası: {e}")
        return

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
