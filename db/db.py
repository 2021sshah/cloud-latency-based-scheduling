import os
import time
from kafka import KafkaConsumer
import sqlite3

# Define configs
broker_ip_port = os.environ.get('KAFKA_BROKER', 'kafka:9092')
topic_name = os.environ.get('KAFKA_TOPIC', 'vlm_data')

# Acquire the consumer
consumer = KafkaConsumer(topic_name, bootstrap_servers=broker_ip_port)

# Function to handle VLM message.
def handle_db(msg):
    conn = sqlite3.connect("caption_image.db")
    cursor = conn.cursor()

    # Create table if it does not exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS vlm_data 
                      (
                          dbID INTEGER PRIMARY KEY, 
                          assigneedID INTEGER UNIQUE, 
                          image_url TEXT, 
                          original_caption TEXT,
                          vlm_caption TEXT, 
                          total_latency REAL
                      )
                   ''')

    # Extract data from message
    data = eval(msg.value.decode('utf-8'))
    assigneedID = data['iter_id']
    image_url = data['image_url']
    original_caption = data['original_caption']
    vlm_caption = data['vlm_caption']
    total_latency = data['total_latency']

    # Check if a record with the assigneedID exists
    cursor.execute("SELECT * FROM vlm_data WHERE assigneedID = ?", (assigneedID,))
    row = cursor.fetchone()

    # Insert data into the database
    cursor.execute('''INSERT OR REPLACE INTO vlm_data (assigneedID, image_url, original_caption, vlm_caption, total_latency)
                      VALUES (?, ?, ?, ?, ?)''', 
                   (assigneedID, image_url, original_caption, vlm_caption, total_latency))
    
    conn.commit()
    conn.close()
    print(f"Inserted record for image row: {assigneedID}")
    

# Display status
print(f"DB Consumer Listening to Kafka Broker ...")

# Continuously read and process messages from Kafka
for msg in consumer:
    handle_db(msg)

# End consumer listener
consumer.close()