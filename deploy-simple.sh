#!/bin/bash

# Upload the current directory to Google Cloud Storage
gcloud storage cp -r . gs://icculus_cloudbuild/source/marker-simple/

# Create a VM with GPU support
gcloud compute instances create marker-gpu-simple \
  --project=icculus \
  --zone=us-east1-b \
  --machine-type=g2-standard-4 \
  --accelerator=type=nvidia-l4,count=1 \
  --maintenance-policy=TERMINATE \
  --image-family=cos-stable \
  --image-project=cos-cloud \
  --boot-disk-size=50GB \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --metadata-from-file=startup-script=simple-startup.sh

# Create a firewall rule to allow HTTP traffic
gcloud compute firewall-rules create allow-http \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:80 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server || echo "Firewall rule already exists"

echo "VM is being created. You can check its status with:"
echo "gcloud compute instances describe marker-gpu-simple --zone=us-east1-b"
echo "Once it's running, you can access it at:"
echo "http://$(gcloud compute instances describe marker-gpu-simple --zone=us-east1-b --format='get(networkInterfaces[0].accessConfigs[0].natIP)')"
