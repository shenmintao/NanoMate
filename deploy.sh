#!/bin/bash
# Deploy script for nanobot with image_gen Gemini support

set -e

echo "==================================================="
echo "  Nanobot Deployment Script"
echo "==================================================="
echo ""

# Check if we're in the right directory
if [ ! -f "Dockerfile" ]; then
    echo "Error: Dockerfile not found. Please run this from the nanobot root directory."
    exit 1
fi

echo "Step 1: Building Docker image..."
docker build -t ghcr.io/shenmintao/nanobot:latest .

echo ""
echo "Step 2: Pushing to GitHub Container Registry..."
docker push ghcr.io/shenmintao/nanobot:latest

echo ""
echo "==================================================="
echo "  Build and push completed successfully!"
echo "==================================================="
echo ""
echo "Next steps on your server:"
echo "  1. ssh your-server"
echo "  2. docker pull ghcr.io/shenmintao/nanobot:latest"
echo "  3. docker restart nanobot-gateway"
echo ""
echo "Or use the remote_deploy.sh script for automatic deployment."
