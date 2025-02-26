#!/bin/bash
set -e

# Variables
PROJECT_ID="icculus"
REGION="us-east1"
ZONE="us-east1-b"
INSTANCE_NAME="marker-gpu-instance"
MACHINE_TYPE="n1-standard-4"
GPU_TYPE="nvidia-tesla-t4"
GPU_COUNT=1
IMAGE_NAME="marker-gpu-api"
REPOSITORY="us-east1-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy"

echo "Building Docker image with GPU support..."
docker build -t ${IMAGE_NAME} -f Dockerfile.gpu .

echo "Tagging the image for Google Container Registry..."
docker tag ${IMAGE_NAME} ${REPOSITORY}/${IMAGE_NAME}:latest

echo "Authenticating with Google Cloud..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev

echo "Pushing the image to Google Container Registry..."
docker push ${REPOSITORY}/${IMAGE_NAME}:latest

echo "Creating a GPU-enabled VM instance..."
gcloud compute instances create ${INSTANCE_NAME} \
  --project=${PROJECT_ID} \
  --zone=${ZONE} \
  --machine-type=${MACHINE_TYPE} \
  --network-interface=network-tier=PREMIUM,subnet=default \
  --maintenance-policy=TERMINATE \
  --provisioning-model=STANDARD \
  --service-account=795058584669-compute@developer.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --accelerator=count=${GPU_COUNT},type=${GPU_TYPE} \
  --tags=http-server,https-server \
  --create-disk=auto-delete=yes,boot=yes,device-name=${INSTANCE_NAME},image=projects/cos-cloud/global/images/cos-stable-109-17800-147-15,mode=rw,size=50,type=pd-balanced \
  --no-shielded-secure-boot \
  --shielded-vtpm \
  --shielded-integrity-monitoring \
  --reservation-affinity=any \
  --metadata=startup-script="#! /bin/bash
# Install NVIDIA drivers
cos-extensions install gpu
mount -o remount,exec /var/lib/nvidia
/var/lib/nvidia/bin/nvidia-smi

# Pull and run the marker-api container
docker pull ${REPOSITORY}/${IMAGE_NAME}:latest
docker run -d --gpus all -p 80:8080 \
  -e PORT=8080 \
  -e GOOGLE_CLOUD_PROJECT=${PROJECT_ID} \
  ${REPOSITORY}/${IMAGE_NAME}:latest
"

echo "Creating firewall rule to allow HTTP traffic..."
gcloud compute firewall-rules create allow-http \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:80 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server

echo "Waiting for VM to initialize..."
sleep 60

echo "Getting the external IP address..."
EXTERNAL_IP=$(gcloud compute instances describe ${INSTANCE_NAME} --zone=${ZONE} --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "Deployment complete!"
echo "Your marker API with GPU support is available at: http://${EXTERNAL_IP}"
echo "It may take a few minutes for the container to start and the API to become available."
