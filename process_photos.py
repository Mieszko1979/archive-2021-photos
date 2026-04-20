import os, json
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS, GPSTAGS

MAX_SIZE = 1600

def get_decimal_from_dms(dms, ref):
    if dms is None or ref is None: return None
    try:
        parts = [float(x) for x in dms]
        val = parts[0] + parts[1]/60.0 + parts[2]/3600.0
        return -float(val) if ref in ['S', 'W'] else float(val)
    except: return None

def process_image(image_path):
    try:
        img = Image.open(image_path)
        exif = img._getexif()
        coords = None
        if exif:
            gps = {}
            for tag, val in exif.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    for t in val: gps[GPSTAGS.get(t, t)] = val[t]
            if "GPSLatitude" in gps:
                coords = {"lat": get_decimal_from_dms(gps["GPSLatitude"], gps.get("GPSLatitudeRef")),
                          "lng": get_decimal_from_dms(gps["GPSLongitude"], gps.get("GPSLongitudeRef"))}
        img = ImageOps.exif_transpose(img)
        img.thumbnail((MAX_SIZE, MAX_SIZE), Image.Resampling.LANCZOS)
        img.save(image_path, "JPEG", quality=80, optimize=True)
        return coords
    except: return None

photos_data = []
for file in os.listdir('.'):
    if file.lower().endswith(('.jpg', '.jpeg')):
        res = process_image(file)
        if res and res["lat"] is not None:
            photos_data.append({"url": file, "lat": res["lat"], "lng": res["lng"]})

photos_data.sort(key=lambda x: x['url'])
with open('photos.json', 'w') as f:
    json.dump(photos_data, f, indent=4)
