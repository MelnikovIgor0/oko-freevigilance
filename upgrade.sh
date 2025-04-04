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

# Build and start new containers
echo "🏗️ Building and starting new containers..."
docker compose up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker compose ps

echo "✅ Deployment completed successfully!" 