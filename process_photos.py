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

def get_gps_from_file(image_path):
    try:
        with Image.open(image_path) as img:
            exif = img._getexif()
            if not exif: return None
            gps = {}
            for tag, val in exif.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    for t in val: gps[GPSTAGS.get(t, t)] = val[t]
            if "GPSLatitude" in gps:
                return {
                    "lat": get_decimal_from_dms(gps["GPSLatitude"], gps.get("GPSLatitudeRef")),
                    "lng": get_decimal_from_dms(gps["GPSLongitude"], gps.get("GPSLongitudeRef", "E"))
                }
    except: return None
    return None

def resize_image(image_path):
    try:
        with Image.open(image_path) as img:
            img = ImageOps.exif_transpose(img)
            if img.width > MAX_SIZE or img.height > MAX_SIZE:
                img.thumbnail((MAX_SIZE, MAX_SIZE), Image.Resampling.LANCZOS)
                img.save(image_path, "JPEG", quality=85, optimize=True)
                return True
    except: return False
    return False

# 1. Читаем уже существующие данные из photos.json, чтобы не потерять их
existing_data = {}
if os.path.exists('photos.json'):
    try:
        with open('photos.json', 'r') as f:
            for item in json.load(f):
                existing_data[item['url']] = {"lat": item['lat'], "lng": item['lng']}
    except: pass

new_photos_list = []
files = [f for f in os.listdir('.') if f.lower().endswith(('.jpg', '.jpeg'))]

for file in files:
    # 2. Если фото уже было в списке — берем старые координаты
    if file in existing_data:
        coords = existing_data[file]
        print(f"Используем сохраненные координаты для {file}")
    else:
        # 3. Если фото новое — достаем GPS и сжимаем
        coords = get_gps_from_file(file)
        if coords:
            print(f"Найдены новые координаты для {file}")
            resize_image(file)
        else:
            print(f"GPS не найден в новом файле {file}")

    if coords:
        new_photos_list.append({"url": file, "lat": coords["lat"], "lng": coords["lng"]})

# 4. Сохраняем обновленный список
new_photos_list.sort(key=lambda x: x['url'])
with open('photos.json', 'w') as f:
    json.dump(new_photos_list, f, indent=4)

print(f"Всего фото в списке: {len(new_photos_list)}")
