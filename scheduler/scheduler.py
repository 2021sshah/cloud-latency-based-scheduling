import os
import random
import json
import time

import logging
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime
import random

from collections import deque
import numpy as np

# Define configs
broker_ip_port = os.environ.get('KAFKA_BROKER', 'kafka:9092')
image_consumer_topic = os.environ.get('KAFKA_IMAGE_TOPIC', 'image_data')
vlm_consumer_topic = os.environ.get('KAFKA_VLM_TOPIC', 'vlm_data')

n_channels = int(os.environ.get('NUM_CHANNELS', 1))
scheduling_topic_prefix = 'scheduling_data_'  # append with channel number
vlm_results_file = 'vlm_results.txt'

# Set up logging
log_file = 'log.txt'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)
logger = logging.getLogger()

# Set up the Kafka Consumer for VLM data
consumer = KafkaConsumer(bootstrap_servers=broker_ip_port)
consumer.subscribe(topics=[image_consumer_topic, vlm_consumer_topic])

# Set up the Kafka Producer for scheduling data
producer = KafkaProducer(bootstrap_servers=broker_ip_port, acks=1)

# Open the VLM latency output file
with open(vlm_results_file, 'w') as f:
    f.write("iter_id, server_num, total_latency\n")

# Lgo status
logger.info(f"Scheduling Consumer Listening to Kafka Broker on topics {image_consumer_topic} and {vlm_consumer_topic} ...")

"""
************************
Random Scheduling
************************
"""

# Helper method for determining which VLM server to pass image_data along
def schedule_server_random():
    return random.randint(1, n_channels)

"""
************************
Roundrobin Scheduling
************************
"""

server_counter = 1  # global server counter
def schedule_server_roundrobin():
    global server_counter
    server_num = server_counter
    server_counter = (server_counter % n_channels) + 1
    return server_num

"""
************************
Ongoing Task Scheduling
************************
"""
server_ongoing = {i: 0 for i in range(1, n_channels + 1)}  # Track active tasks per server
def schedule_server_ongoing():
    global server_ongoing

    # Handle edge case
    container = {}
    for server, tasks in server_ongoing.items():

        server1_tasks_ub = 3
        if server == 1 and server_ongoing_tasks[server] >= server1_tasks_ub:
            continue

        server2_tasks_ub = 5
        if server == 2 and server_ongoing_tasks[server] >= server2_tasks_ub:
            continue

        container[server] = tasks


    # Find the server with the least load
    server_num = min(container, key=container.get)
    server_ongoing[server_num] += 1
    return server_num

def finish_task_ongoing(server_num):
    global server_ongoing
    # Decrease the load when the task is finished
    server_ongoing[server_num] -= 1

"""
******************************
Historical Average Scheduling
******************************
"""

server_latencies = {i: [] for i in range(1, n_channels + 1)}  # Store latency history per server
def schedule_server_historical():
    # Calculate the average latency for each server
    avg_latencies = {server: sum(latencies)/len(latencies) if len(latencies) >= 10 else -1 for server, latencies in server_latencies.items()}
    if -1 in avg_latencies.values():
        server_num = schedule_server_roundrobin()
    else:
        server_num = min(avg_latencies, key=avg_latencies.get)
    return server_num

def update_latency_historical(server_num, latency):
    # Record the latency for this server
    server_latencies[server_num].append(latency)

"""
**********************************
Time Series Forecasting Scheduling
**********************************
"""

server_latencies = {i: deque(maxlen=10) for i in range(1, n_channels + 1)}  # Last 10 latencies per server
server_ongoing_tasks = {i: 0 for i in range(1, n_channels + 1)}  # Active tasks per server
last_scheduled_time = {i: 0 for i in range(1, n_channels + 1)}   # Tracker of scheduling time

def schedule_server_forecasting():
    """
    Schedule a server using combined historical and ongoing tasks.
    Predict latency using fast linear regression and pick the server with the lowest forecasted latency.
    """
    global server_latencies, server_ongoing_tasks, last_scheduled_time
    
    forecasted_latencies = {}
    time_gaps = {}

    # Handle not enough historical data
    lengths_bin = {0 if len(latencies) >= 10 else 1 for latencies in server_latencies.values()}
    if sum(lengths_bin):

        # Roundrobin scheduling
        server_num = schedule_server_roundrobin()
        
        # Increment the task count for the selected server
        server_ongoing_tasks[server_num] += 1
        last_scheduled_time[server_num] = datetime.utcnow()
        return server_num
    
    # Perform fast polynomial regression (best fit => degree 1) to predict additional latency
    for server, latencies in server_latencies.items():

        X = np.array(range(1, len(latencies) + 1))  # Number of tasks (independent variable)
        y = np.array(latencies)  # Latency values (dependent variable)
        A = np.vstack([X, np.ones(len(X))]).T  # Design matrix for linear regression
        m, c = np.linalg.lstsq(A, y, rcond=None)[0]  # Solve for slope and intercept
            
        # Predict latency for one additional scheduled task
        current_tasks = server_ongoing_tasks[server]
        forecasted_latencies[server] = m * (current_tasks + 1) + c

        # Compute time gap to last scheduling
        current_time = datetime.utcnow()
        time_gaps[server] = (current_time - last_scheduled_time[server]).total_seconds()

        # Handle edge case => large time gap
        task_lb, time_ub = 2, 10
        if server_ongoing_tasks[server] < task_lb or time_gaps[server] > time_ub:
            # Increment the task count for the respective server
            server_ongoing_tasks[server] += 1
            last_scheduled_time[server] = datetime.utcnow()
            return server

    # Weighted heuristic of forecasted latencies and time gaps
    weights = {}
    for server in server_latencies.keys():
        latency_score = forecasted_latencies[server]
        neg_time_gap_score = -time_gaps[server]  # Negative to favor larger gaps
        weights[server] = latency_score + neg_time_gap_score  # Weighted combination

    # Choose the server with the lowest weighted score
    server_num = min(weights, key=weights.get)
    
    # Increment the task count for the selected server
    server_ongoing_tasks[server_num] += 1
    last_scheduled_time[server_num] = datetime.utcnow()
    return server_num

def finish_task_forecasting(server_num):
    """
    Decrement the count of ongoing tasks when a task finishes.
    """
    global server_ongoing_tasks
    server_ongoing_tasks[server_num] -= 1

def update_latency_forecasting(server_num, latency):
    """
    Update the latency history for a server.
    """
    global server_latencies
    server_latencies[server_num].append(latency)


"""
MAIN EXECUTION BELOW
"""

# Continuously consume and process messages
for msg in consumer:
    message = json.loads(msg.value.decode('utf-8'))

    # Distinguish message received as from producer
    if msg.topic == image_consumer_topic:

        # Log received image
        logger.info(f"Message from producer received -- image row {message['iter_id']}")

        # Determine VLM channel based on scheduling algorithm
        server_num = schedule_server_ongoing()
        server_channel = f"{scheduling_topic_prefix}{server_num}"
        
        # Record start time after scheduling
        message['send_time'] = datetime.utcnow().isoformat()
        message['server_num'] = server_num
        
        # Send to selected VLM channel
        producer.send(server_channel, value=json.dumps(message).encode('utf-8'))
        producer.flush()

    # Distinguish message received as from VLM server
    else:

        # Log the original vs vlm-generated captions
        logger.info(f"Message from vlm received -- image row {message['iter_id']}")
        logger.info(f"Original Caption: {message['original_caption']}")
        logger.info(f"Generated Caption: {message['vlm_caption']}\n")

        # Extract the necessary fields from the message
        iter_id = message.get('iter_id')
        server_num = message.get('server_num')
        total_latency = message.get('total_latency')

        # Update tacker
        finish_task_forecasting(server_num)
        update_latency_forecasting(server_num, total_latency)

        # Log results to vlm_results.txt
        with open(vlm_results_file, 'a') as f:
            f.write(f"{iter_id}, {server_num}, {total_latency}\n")
        
        # Log
        logger.info(f"VLM processed => image id: {iter_id}, server_num: {server_num}, total_latency: {total_latency}s")

# Close the consumer and producer
consumer.close()
producer.close()
