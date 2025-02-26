# Deploying Marker on RunPod

## Prerequisites
- A running RunPod instance with GPU support
- Access to the Web Terminal or SSH

## Steps to Deploy

1. **Access your RunPod instance**
   - Go to your RunPod dashboard
   - Find your pod and click on "Connect"
   - In the Connection Options dialog, click "Start" under Web Terminal
   - This will open a terminal in your browser

2. **Clone the repository**
   - In the Web Terminal, run:
   ```bash
   cd /workspace
   git clone https://github.com/yourusername/marker.git
   cd marker
   ```
   - Alternatively, you can upload your local files using the RunPod file browser

3. **Build the Docker image**
   - In the Web Terminal, run:
   ```bash
   docker build -t marker-gpu-api -f Dockerfile.gpu .
   ```

4. **Run the container with GPU support**
   - In the Web Terminal, run:
   ```bash
   docker run -d --gpus all -p 8080:8080 \
     -e PORT=8080 \
     marker-gpu-api
   ```

5. **Expose the API endpoint**
   - Go back to the RunPod dashboard
   - Click on "Connect" for your pod
   - In the Connection Options dialog, under "HTTP Services"
   - Click "Add HTTP Service"
   - Enter:
     - Internal Port: 8080
     - Service Name: Marker API
   - Click "Add"

6. **Access the API**
   - Once the service is added, you'll see a URL in the HTTP Services section
   - Click on the URL to access your Marker API

## Troubleshooting

If you encounter any issues:

1. **Check container logs**
   ```bash
   docker ps  # Get the container ID
   docker logs <container_id>
   ```

2. **Check GPU availability**
   ```bash
   nvidia-smi
   ```

3. **Verify port mapping**
   ```bash
   docker ps
   ```
   Ensure the container is properly mapping port 8080
