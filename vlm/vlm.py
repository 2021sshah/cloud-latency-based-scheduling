import os
import time
import json
import requests
import logging

from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime
from PIL import Image
import moondream as md

# Define configs
broker_ip_port = os.environ.get('KAFKA_BROKER', 'kafka:9092')
consumer_topic_prefix = os.environ.get('KAFKA_CONSUMER_TOPIC', 'scheduling_data')
channel_num = os.environ.get('KAFKA_CHANNEL_NUM', "1")

consumer_topic_name = f"{consumer_topic_prefix}_{channel_num}"
producer_topic_name = os.environ.get('KAFKA_PRODUCER_TOPIC', 'vlm_data')

# Set up logging
log_file = '/tmp/log.txt'  # You can change this path if needed
logging.basicConfig(
    level=logging.INFO,  # Adjust the log level to INFO for normal logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]  # Log to both file and console
)
logger = logging.getLogger()

# Display the consumer topic name
logger.info(f"Consumer topic name: {consumer_topic_name}")

# Acquire the consumer and producer
consumer = KafkaConsumer(consumer_topic_name, bootstrap_servers=broker_ip_port)
producer = KafkaProducer(bootstrap_servers=broker_ip_port, acks=1)

# Display status
logger.info(f"VLM Consumer Listening to Kafka Broker ...")

# Initialize Moondream VLM model
model = md.VL("moondream-latest-int4.bin")

# Path to temporarily save images downloaded from URLs
temp_image_path = "temp_image.jpg"

# Open file to record processing times
output_file = 'vlm_server_times.txt'
with open(output_file, 'w') as f:
    f.write("iter_id, total_time\n")

# Function to download an image from a URL and save it locally
def download_image(url, save_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        logger.info(f"Downloaded image from {url}")
        return save_path
    else:
        logger.error(f"Failed to download image from {url}, status code: {response.status_code}")
        return None

# Function to perform captioning with Moondream VLM
def generate_caption(image_path):
    image = Image.open(image_path)
    try:
        encoded_image = model.encode_image(image)
        caption = model.caption(encoded_image)["caption"]
        logger.info("Generated caption successfully.")
    except Exception as e:
        logger.error(f"Error in generating caption: {e}")
        caption = ""
    return caption

"""
MAIN EXECUTION BELOW
"""

# Receive and process messages
for msg in consumer:
    message = json.loads(msg.value.decode('utf-8'))

    # Extract fields from the message
    iter_id = message['iter_id']
    image_url = message['image_url']
    original_caption = message['caption']
    send_time = datetime.fromisoformat(message['send_time'])

    # Download the image
    downloaded_image_path = download_image(image_url, temp_image_path)
    if downloaded_image_path is None:
        continue  # Skip if download failed

    # Generate a caption with the VLM model
    vlm_caption = generate_caption(downloaded_image_path)

    # Calculate total processing time
    current_time = datetime.utcnow()
    total_latency = (current_time - send_time).total_seconds()

    # Log the iter_id and total latency
    with open(output_file, 'a') as f:
        f.write(f"{iter_id}, {total_latency}\n")

    # Log the update status
    logger.info(f"Processed iter_id: {iter_id}, total_latency: {total_latency}s")

    # Update message with VLM caption and total latency
    message['original_caption'] = original_caption
    message['vlm_caption'] = vlm_caption
    message['total_latency'] = total_latency

    # Send the updated message to the inference topic
    producer.send(producer_topic_name, value=json.dumps(message).encode('utf-8'))
    producer.flush()

    # Log the sending status
    logger.info(f"Sent image {iter_id} to DB")

# Close consumer and producer
consumer.close()
producer.close()