import os
import requests
import zipfile
from io import BytesIO
from pycocotools.coco import COCO
from PIL import Image

# Download the annotations ZIP file using requests
zip_url = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
response = requests.get(zip_url)

# Check if the download was successful
if response.status_code == 200:
    print("Downloaded annotations ZIP file.")
else:
    print("Failed to download annotations.")
    exit(1)

# Unzip the file and extract the specific JSON file
with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
    # Extract the required file
    json_filename = "annotations/captions_val2017.json"
    zip_file.extract(json_filename)

# Load the JSON file into COCO
coco = COCO(json_filename)

print("MS-COCO dataset loaded with pycocotools")


# Path to temporarily save images downloaded from URLs
temp_image_path = "temp_image.jpg"

# Function to download an image from a URL and save it locally
def download_image(url, save_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return save_path
    else:
        return None

# Function to resize an image in memory
def resize_image_in_memory(iter_id, image_path, size=(256, 256)):
    try:
        image = Image.open(image_path)
        print(f"original size = {image.size}")
        resized_image = image.resize(size)
        return f"MS-COCO image {iter_id} successfully resized."
    except Exception as e:
        print(e)
        return f"{iter_id} image FAILED to resize!"


# Step 4: Use the COCO API (example: loading image ids)
img_ids = coco.getImgIds()[:10]  # Just getting first 10 image IDs for demo
ann_ids = coco.getAnnIds(imgIds=img_ids)

for i, img_id in enumerate(img_ids):
    print(f"----------Row {i+1}----------")

    # Get image metadata
    img_info = coco.loadImgs([img_id])[0]
    image_url = img_info['coco_url']
    print(f"image url = {image_url}")

    # Get caption (take the first caption for simplicity)
    ann_info = coco.loadAnns(coco.getAnnIds(imgIds=[img_id]))
    caption = ann_info[0]['caption'] if ann_info else ""
    print(f"original caption = {caption}\n")

    # Download the image
    downloaded_image_path = download_image(image_url, temp_image_path)
    if downloaded_image_path is None:
        continue  # Skip if download failed

    # Resize the image in memory and record caption
    resize_caption = resize_image_in_memory(i, downloaded_image_path)
    print(f"resize caption = {resize_caption}")

