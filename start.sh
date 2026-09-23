#!/bin/bash

# Resume Screening AI - Startup Script

echo "Starting Resume Screening AI..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from env.example..."
    cp env.example .env
    echo "Please edit .env file with your configuration"
fi

# Create uploads directory
mkdir -p uploads

# Start Docker Compose
echo "Starting Docker containers..."
docker compose up --build
