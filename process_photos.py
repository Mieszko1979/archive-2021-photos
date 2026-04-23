import os
import json
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS, GPSTAGS

MAX_SIZE = 1600

def get_decimal_from_dms(dms, ref):
    if dms is None or ref is None: return None
    try:
        parts = []
        for x in dms:
            if isinstance(x, tuple) or hasattr(x, 'numerator'):
                parts.append(float(x[0]) / float(x[1]) if isinstance(x, tuple) else float(x))
            else:
                parts.append(float(x))
        val = parts[0] + parts[1]/60.0 + parts[2]/3600.0
        return -val if ref in ['S', 'W'] else val
    except: return None

def process_image(image_path):
    try:
        # Используем контекстный менеджер, чтобы файл всегда закрывался правильно
        with Image.open(image_path) as img:
            # 1. Извлекаем GPS
            exif = img._getexif()
            coords = None
            if exif:
                gps = {}
                for tag, val in exif.items():
                    decoded = TAGS.get(tag, tag)
                    if decoded == "GPSInfo":
                        for t in val: gps[GPSTAGS.get(t, t)] = val[t]
                if "GPSLatitude" in gps:
                    coords = {
                        "lat": get_decimal_from_dms(gps["GPSLatitude"], gps.get("GPSLatitudeRef")),
                        "lng": get_decimal_from_dms(gps["GPSLongitude"], gps.get("GPSLongitudeRef", "E"))
                    }

            # 2. Обработка изображения (разворот и сжатие если нужно)
            img = ImageOps.exif_transpose(img)
            if img.width > MAX_SIZE or img.height > MAX_SIZE:
                img.thumbnail((MAX_SIZE, MAX_SIZE), Image.Resampling.LANCZOS)
                img.save(image_path, "JPEG", quality=85, optimize=True)
            
            return coords
    except Exception as e:
        print(f"Ошибка в {image_path}: {e}")
        return None

photos_data = []
# Сканируем папку и ВСЕГДА обновляем список тех, у кого есть координаты
for file in os.listdir('.'):
    if file.lower().endswith(('.jpg', '.jpeg')):
        res = process_image(file)
        if res and res["lat"] is not None:
            photos_data.append({"url": file, "lat": res["lat"], "lng": res["lng"]})

# Записываем результат
photos_data.sort(key=lambda x: x['url'])
with open('photos.json', 'w') as f:
    json.dump(photos_data, f, indent=4)

print(f"Обработка завершена. Найдено фото с GPS: {len(photos_data)}")
