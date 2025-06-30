#!/bin/bash

# AlgoTrader Docker Runner Script
# Usage: ./run-docker.sh [script_name]

set -e

# Default script if none provided
SCRIPT_NAME=${1:-get_allassetcap.py}

echo "🐳 Starting AlgoTrader Docker Container"
echo "📝 Running: $SCRIPT_NAME"
echo "=" * 50

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "💡 Create a .env file with your API keys before running."
    exit 1
fi

# Build the image if it doesn't exist
if [[ "$(docker images -q algotradar-scraper 2> /dev/null)" == "" ]]; then
    echo "🔨 Building Docker image..."
    docker build -t algotradar-scraper .
fi

# Run the container
echo "🚀 Running scraper..."
docker run --rm \
    --name algotradar-runner \
    -v "$(pwd)/.env:/app/.env:ro" \
    -v "$(pwd)/logs:/app/logs" \
    --memory=2g \
    --cpus=1.0 \
    algotradar-scraper python "$SCRIPT_NAME"

echo "✅ Scraper completed!" 