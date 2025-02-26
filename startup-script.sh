#!/bin/bash
# Install NVIDIA drivers
cos-extensions install gpu
mount -o remount,exec /var/lib/nvidia
/var/lib/nvidia/bin/nvidia-smi

# Pull and run the marker-gpu-api container
docker pull us-east1-docker.pkg.dev/icculus/cloud-run-source-deploy/marker-gpu-api:latest
docker run -d --gpus all -p 80:8080 \
  -e PORT=8080 \
  -e GOOGLE_CLOUD_PROJECT=icculus \
  us-east1-docker.pkg.dev/icculus/cloud-run-source-deploy/marker-gpu-api:latest
