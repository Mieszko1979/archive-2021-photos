import os
import json
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS, GPSTAGS

# Устанавливаем 1600 пикселей по широкой стороне
MAX_SIZE = 1600

def get_decimal_from_dms(dms, ref):
    if dms is None or ref is None:
        return None
    degrees = dms[0]
    minutes = dms[1] / 60.0
    seconds = dms[2] / 3600.0
    if ref in ['S', 'W']:
        return -float(degrees + minutes + seconds)
    return float(degrees + minutes + seconds)

def process_image(image_path):
    try:
        img = Image.open(image_path)
        
        # 1. Извлекаем GPS
        exif_data = img._getexif()
        coords = None
        if exif_data:
            gps_info = {}
            for tag, value in exif_data.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_info[sub_decoded] = value[t]
            
            if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
                lat = get_decimal_from_dms(gps_info["GPSLatitude"], gps_info.get("GPSLatitudeRef"))
                lng = get_decimal_from_dms(gps_info["GPSLongitude"], gps_info.get("GPSLongitudeRef"))
                if lat is not None and lng is not None:
                    coords = {"lat": lat, "lng": lng}

        # 2. Исправляем поворот и уменьшаем размер
        img = ImageOps.exif_transpose(img)
        img.thumbnail((MAX_SIZE, MAX_SIZE), Image.Resampling.LANCZOS)
        
        # 3. Сохраняем сжатую копию
        img.save(image_path, "JPEG", quality=80, optimize=True)
        
        return coords
    except Exception as e:
        print(f"Ошибка в файле {image_path}: {e}")
    return None

photos_data = []
# Проходим по всем файлам
for file in os.listdir('.'):
    if file.lower().endswith(('.jpg', '.jpeg')):
        print(f"Обработка {file}...")
        res = process_image(file)
        if res:
            photos_data.append({
                "url": file,
                "lat": res["lat"],
                "lng": res["lng"]
            })

# Сортируем по имени файла и записываем результат
photos_data.sort(key=lambda x: x['url'])
with open('photos.json', 'w') as f:
    json.dump(photos_data, f, indent=4)

print("Готово! Список photos.json обновлен.")
