import os
import time
import json
import logging

from kafka import KafkaProducer
import requests
import zipfile
from io import BytesIO
from pycocotools.coco import COCO

# Define configs
broker_ip_port = os.environ.get('KAFKA_BROKER', 'kafka:9092')
topic_name = os.environ.get('KAFKA_TOPIC', 'image_data')
n_images = 500  # Total images to send

# Set up logging
log_file = 'log.txt'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]  # Log to both file and console
)
logger = logging.getLogger()

# Acquire the producer
producer = KafkaProducer(bootstrap_servers=broker_ip_port, acks=1)

logger.info("Producer connected to Kafka Broker")

# Download the annotations ZIP file using requests
zip_url = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
response = requests.get(zip_url)

# Check if the download was successful
if response.status_code == 200:
    logger.info("Downloaded annotations ZIP file.")
else:
    logger.error("Failed to download annotations.")
    exit(1)

# Unzip the file and extract the specific JSON file
with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
    # Extract the required file
    json_filename = "annotations/captions_val2017.json"
    zip_file.extract(json_filename, path='/tmp')

# Load the JSON file into COCO
extracted_json_path = os.path.join('/tmp', json_filename)
coco = COCO(extracted_json_path)

# Get image and caption IDs
img_ids = coco.getImgIds()[:n_images]
ann_ids = coco.getAnnIds(imgIds=img_ids)

logger.info("MS-COCO dataset loaded with pycocotools")
done = False

# Continuous execution loop
while True:

    # Stop producing data after sending once
    if done:
        continue

    # Iterate through all data
    for i, img_id in enumerate(img_ids):
        logger.info(f"Sent row {i}")

        # Get image metadata
        img_info = coco.loadImgs([img_id])[0]
        image_url = img_info['coco_url']

        # Get caption (take the first caption for simplicity)
        ann_info = coco.loadAnns(coco.getAnnIds(imgIds=[img_id]))
        caption = ann_info[0]['caption'] if ann_info else ""

        # Structure message as JSON
        contents = {
            'iter_id': i,
            'image_url': image_url,
            'caption': caption,
        }

        # Send encoded JSON (serialized to bytes)
        producer.send(topic_name, value=json.dumps(contents).encode('utf-8'))
        producer.flush()

        # Delay between messages
        time.sleep(0.1)
    
    # Stop sending data
    done = True

# Close producer
producer.close()
