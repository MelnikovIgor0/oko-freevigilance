#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting deployment process..."

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull

# Docker Compose operations
echo "🐳 Managing Docker containers with Compose..."

# Stop and remove existing containers
echo "🛑 Stopping and removing existing containers..."
docker compose down

# Remove all unused containers, images, and volumes
echo "🧹 Removing unused containers, images, and volumes..."
docker system prune -af

# Build and start new containers
echo "🏗️ Building and starting new containers..."
docker compose up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 30

# Starting service cron
echo "Starting service cron..."
CONTAINER_ID=$(docker ps --filter "name=api" --format "{{.ID}}")
docker exec $CONTAINER_ID service cron start

# Check if services are running
echo "🔍 Checking service status..."
docker compose ps

echo "✅ Deployment completed successfully!" 