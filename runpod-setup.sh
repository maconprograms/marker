#!/bin/bash
# Script to set up and run marker on RunPod
# Run this script on the RunPod instance after uploading the code

# Check if NVIDIA GPU is available
echo "Checking GPU availability..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "ERROR: NVIDIA drivers not found. Make sure you're using a GPU-enabled pod."
    exit 1
fi

nvidia-smi

# Navigate to the marker directory
cd /workspace/marker || {
    echo "ERROR: /workspace/marker directory not found."
    echo "Make sure you've uploaded the code and extracted it correctly."
    exit 1
}

# Build the Docker image
echo "Building Docker image with GPU support..."
docker build -t marker-gpu-api -f Dockerfile.gpu .

# Check if there's already a container running on port 8080
if docker ps | grep -q "8080->8080"; then
    echo "Stopping existing container on port 8080..."
    docker stop $(docker ps -q --filter "publish=8080")
fi

# Run the container with GPU support
echo "Starting marker container with GPU support..."
docker run -d --gpus all -p 8080:8080 \
  -e PORT=8080 \
  marker-gpu-api

# Show running containers
echo "Running containers:"
docker ps

echo "Marker API is now running on port 8080"
echo "To access it, go to the RunPod dashboard, click 'Connect' on your pod,"
echo "and add an HTTP Service mapping port 8080 to a name like 'Marker API'"
