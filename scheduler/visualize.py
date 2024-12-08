import pandas as pd
import matplotlib.pyplot as plt

# Load the data and clean column names
df = pd.read_csv('vlm_results.txt')
# Clean column names by stripping whitespace
df.columns = df.columns.str.strip()

# Filter out rows with iter_id > 500
df = df[df['iter_id'] <= 500]

# Create figure and subplots
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('Server Latencies Over Time', fontsize=16)

# Plot each server's data
servers = [1, 2, 3, 4]
axes = [ax1, ax2, ax3, ax4]

for server, ax in zip(servers, axes):
    # Filter data for this server
    server_data = df[df['server_num'] == server]
    
    # Sort by iter_id to ensure correct timeline
    server_data = server_data.sort_values('iter_id')
    
    # Plot
    ax.scatter(server_data['iter_id'], server_data['total_latency'])
    ax.set_title(f'Server {server}')
    ax.set_xlabel('Iteration ID')
    ax.set_ylabel('Latency (s)')
    ax.grid(True)

# Ensure all plots have the same x and y limits
x_min = df['iter_id'].min()
x_max = df['iter_id'].max()
y_min = df['total_latency'].min()
y_max = df['total_latency'].max()

for ax in axes:
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

# Adjust layout to prevent overlap
plt.tight_layout()
plt.savefig('server_latencies.png')