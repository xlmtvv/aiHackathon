from typing import List, Tuple
import random
from fastapi import FastAPI, File, UploadFile
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS, GPSTAGS, IFD
from pillow_heif import register_heif_opener    # for heif images
import asyncio

register_heif_opener()

app = FastAPI()

async def fraction_to_float(fraction):
    return float(fraction.numerator) / float(fraction.denominator)

async def extract_coordinates(exif_data):


    async def dms_to_decimal_degrees(degrees, minutes, seconds):
        return degrees + minutes / 60 + seconds / 3600

    # Get latitude components
    lat_degrees = exif_data['GPSLatitude'][0]
    lat_minutes = exif_data['GPSLatitude'][1]
    lat_seconds = exif_data['GPSLatitude'][2]
    lat_ref = exif_data['GPSLatitudeRef']

    # Get longitude components
    lon_degrees = exif_data['GPSLongitude'][0]
    lon_minutes = exif_data['GPSLongitude'][1]
    lon_seconds = exif_data['GPSLongitude'][2]
    lon_ref = exif_data['GPSLongitudeRef']


    latitude = await dms_to_decimal_degrees(lat_degrees, lat_minutes, lat_seconds)
    if lat_ref == 'S':
        latitude = -latitude

    longitude = await dms_to_decimal_degrees(lon_degrees, lon_minutes, lon_seconds)
    if lon_ref == 'W':
        longitude = -longitude

    latitude = await fraction_to_float(latitude)
    longitude = await fraction_to_float(longitude)

    return (latitude, longitude)  



async def mock_ai_model(img) -> Tuple[bool, Tuple]:
    found_litter = random.choice([True, False])


    exif = img.getexif()

    resolve = GPSTAGS

    ifd = exif.get_ifd(IFD.GPSInfo)

    tags = {}
    for k, v in ifd.items():
        tag = resolve.get(k, k)
        tags[tag] = v


    metadata = await extract_coordinates(tags)


    return found_litter, metadata

@app.post("/detect_litter/")
async def detect_litter(file: UploadFile = File(...)) -> dict:

    
    image = Image.open(file.file)
    found_litter, coordinates = await mock_ai_model(image)

    ai_task = asyncio.create_task(mock_ai_model(image))

    found_litter, coordinates = await ai_task  

    if found_litter:
        coordinates = coordinates if coordinates else 'No coords'
        print({"isLitter": "true", "coordinates": coordinates})
        return {"isLitter": "true", "coordinates": coordinates}
    else:
        print({"isLitter": "false"})
        return {"isLitter": "false"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5500)