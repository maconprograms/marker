#!/bin/bash
# Script to upload marker code to RunPod

# RunPod connection details
RUNPOD_IP="63.141.33.46"
RUNPOD_PORT="22101"

# Create a tar archive of the current directory
echo "Creating archive of marker code..."
tar -czf marker.tar.gz .

# Upload the code to RunPod
echo "Uploading code to RunPod..."
scp -P $RUNPOD_PORT marker.tar.gz root@$RUNPOD_IP:/workspace/

echo "Upload complete!"
echo "Now connect to your RunPod using the Web Terminal and run:"
echo "cd /workspace"
echo "mkdir -p /workspace/marker"
echo "tar -xzf marker.tar.gz -C /workspace/marker"
echo "cd marker"
echo "docker build -t marker-gpu-api -f Dockerfile.gpu ."
echo "docker run -d --gpus all -p 8080:8080 -e PORT=8080 marker-gpu-api"
