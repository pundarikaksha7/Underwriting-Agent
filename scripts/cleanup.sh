#!/bin/bash
# Stop and cleanup

echo "Stopping all services..."
docker-compose down

echo "✓ Services stopped and cleaned up"
