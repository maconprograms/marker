#!/bin/bash
set -e

PROJECT_ID="icculus"
REGION="us-east1"
ZONE="us-east1-b"
INSTANCE_NAME="marker-gpu-instance"

echo "Submitting Cloud Build job to deploy marker-api with GPU support..."
gcloud builds submit --config=cloudbuild.yaml

echo "Waiting for VM to initialize (2 minutes)..."
sleep 120

echo "Getting the external IP address..."
EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

if [ -z "$EXTERNAL_IP" ]; then
  echo "Error: Could not get external IP address. VM might not be ready yet."
  exit 1
fi

echo "Deployment complete!"
echo "Your marker API with GPU support is available at: http://$EXTERNAL_IP"

echo "Waiting for container to start (30 seconds)..."
sleep 30

echo "Testing health endpoint..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://$EXTERNAL_IP/health)

if [ "$HEALTH_CHECK" == "200" ]; then
  echo "✅ Health check successful! The API is up and running."
  echo "You can test the API by sending a POST request to http://$EXTERNAL_IP/process"
else
  echo "❌ Health check failed with status code: $HEALTH_CHECK"
  echo "Checking VM logs..."
  gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="sudo docker logs \$(sudo docker ps -q)"
fi
