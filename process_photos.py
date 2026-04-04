import os, json
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS, GPSTAGS

MAX_SIZE = 1600

def get_decimal_from_dms(dms, ref):
    degrees = dms[0]
    minutes = dms[1] / 60.0
    seconds = dms[2] / 3600.0
    if ref in ['S', 'W']: return -float(degrees + minutes + seconds)
    return float(degrees + minutes + seconds)

def process_image(image_path):
    try:
        img = Image.open(image_path)
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
                lat = get_decimal_from_dms(gps_info["GPSLatitude"], gps_info["GPSLatitudeRef"])
                lng = get_decimal_from_dms(gps_info["GPSLongitude"], gps_info["GPSLongitudeRef"])
                coords = {"lat": lat, "lng": lng}
        img = ImageOps.exif_transpose(img)
        img.thumbnail((MAX_SIZE, MAX_SIZE), Image.Resampling.LANCZOS)
        img.save(image_path, "JPEG", quality=80, optimize=True)
        return coords
    except: return None

photos_data = []
for file in os.listdir('.'):
    if file.lower().endswith(('.jpg', '.jpeg')):
        coords = process_image(file)
        if coords:
            photos_data.append({"url": file, "lat": coords["lat"], "lng": coords["lng"]})

with open('photos.json', 'w') as f:
    json.dump(sorted(photos_data, key=lambda x: x['url']), f, indent=4)
