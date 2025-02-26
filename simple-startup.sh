#!/bin/bash
# Install NVIDIA drivers
cos-extensions install gpu
mount -o remount,exec /var/lib/nvidia
/var/lib/nvidia/bin/nvidia-smi

# Create a directory for our application
mkdir -p /tmp/marker
cd /tmp/marker

# Copy the necessary files from Google Cloud Storage
gsutil -m cp -r gs://icculus_cloudbuild/source/* .

# Build the Docker image
docker build -t marker-gpu-api -f Dockerfile.gpu .

# Run the container
docker run -d --gpus all -p 80:8080 \
  -e PORT=8080 \
  -e GOOGLE_CLOUD_PROJECT=icculus \
  marker-gpu-api
