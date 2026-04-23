import os
import json
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS, GPSTAGS

MAX_SIZE = 1600

def get_decimal_from_dms(dms, ref):
    if dms is None or ref is None: return None
    try:
        parts = [float(x[0])/float(x[1]) if isinstance(x, tuple) else float(x) for x in dms]
        val = parts[0] + parts[1]/60.0 + parts[2]/3600.0
        return -val if ref in ['S', 'W'] else val
    except: return None

def process_image(image_path):
    try:
        # Открываем изображение
        img = Image.open(image_path)
        exif_raw = img.info.get('exif') # Сохраняем "сырые" метаданные
        
        # 1. Извлекаем GPS
        exif_data = img._getexif()
        coords = None
        if exif_data:
            gps = {}
            for tag, val in exif_data.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    for t in val: gps[GPSTAGS.get(t, t)] = val[t]
            
            if "GPSLatitude" in gps:
                coords = {
                    "lat": get_decimal_from_dms(gps["GPSLatitude"], gps.get("GPSLatitudeRef")),
                    "lng": get_decimal_from_dms(gps["GPSLongitude"], gps.get("GPSLongitudeRef", "E"))
                }

        # 2. Сжатие и поворот
        img = ImageOps.exif_transpose(img)
        if img.width > MAX_SIZE or img.height > MAX_SIZE:
            img.thumbnail((MAX_SIZE, MAX_SIZE), Image.Resampling.LANCZOS)
            # СОХРАНЯЕМ С EXIF (чтобы координаты не стерлись в будущем)
            if exif_raw:
                img.save(image_path, "JPEG", quality=85, optimize=True, exif=exif_raw)
            else:
                img.save(image_path, "JPEG", quality=85, optimize=True)
            print(f"Обработано и сжато: {image_path}")
        
        return coords
    except Exception as e:
        print(f"Ошибка в {image_path}: {e}")
        return None

# ГЛАВНЫЙ ЦИКЛ
photos_data = []
files = [f for f in os.listdir('.') if f.lower().endswith(('.jpg', '.jpeg'))]

for file in files:
    res = process_image(file)
    if res and res["lat"] is not None:
        photos_data.append({"url": file, "lat": res["lat"], "lng": res["lng"]})
        print(f"Добавлено: {file} ({res['lat']}, {res['lng']})")

# Записываем photos.json
photos_data.sort(key=lambda x: x['url'])
with open('photos.json', 'w') as f:
    json.dump(photos_data, f, indent=4)

print(f"Завершено! В списке {len(photos_data)} фото.")
