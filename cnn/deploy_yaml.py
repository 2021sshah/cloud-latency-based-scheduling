import os
import subprocess

# Define N_CHANNELS and server_delays config
N_CHANNELS = 4
server_delays = [2, 1, 0.1, 0.1]

# Base YAML template as a Python string
yaml_template = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: cnn-{channel_num}
  namespace: default
  labels:
    app: cnn
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cnn
  template:
    metadata:
      labels:
        app: cnn
    spec:
      nodeSelector:
        dedicated: vlm-node
      containers:
        - name: cnn
          image: 192.168.5.182:5000/cnn:latest
          ports:
            - containerPort: 5000
          env:
            - name: KAFKA_BROKER
              value: "kafka-service:9092"
            - name: KAFKA_CONSUMER_TOPIC
              value: "scheduling_data"
            - name: CHANNEL_NUM
              value: "{channel_num}"
            - name: SERVER_DELAY
              value: "{server_delay}"
            - name: KAFKA_PRODUCER_TOPIC
              value: "vlm_data"
            - name: ENVIRONMENT
              value: "production"
"""

# Directory to store generated YAML files
output_dir = "generated_yamls"
os.makedirs(output_dir, exist_ok=True)

# Loop to generate and apply YAML files
for channel_num in range(1, N_CHANNELS + 1):
    # Index server delay
    server_delay = server_delays[channel_num - 1]

    # Generate YAML content
    yaml_content = yaml_template.format(channel_num=channel_num, server_delay=server_delay)
    
    # Write the YAML content to a file
    yaml_file = os.path.join(output_dir, f"cnn-{channel_num}.yaml")
    with open(yaml_file, "w") as f:
        f.write(yaml_content)
    
    # Apply the YAML using kubectl
    try:
        subprocess.run(["kubectl", "apply", "-f", yaml_file], check=True)
        print(f"Successfully deployed for channel_num={channel_num}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to deploy for channel_num={channel_num}. Error: {e}")
