#!/bin/bash
# Development setup script

set -e

echo "═══════════════════════════════════════════════════════════"
echo "  Underwriting Agent - Development Setup"
echo "═══════════════════════════════════════════════════════════"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose found${NC}"

# Create environment file if it doesn't exist
echo -e "${BLUE}Setting up environment...${NC}"

if [ ! -f "backend/.env" ]; then
    echo "Creating backend/.env from template..."
    cp backend/.env.example backend/.env
    echo -e "${GREEN}✓ Created backend/.env${NC}"
else
    echo -e "${GREEN}✓ backend/.env already exists${NC}"
fi

# Start Docker containers
echo -e "${BLUE}Starting Docker containers...${NC}"
docker-compose up -d

# Wait for containers to be ready
echo -e "${BLUE}Waiting for services to be ready...${NC}"
sleep 10

# Initialize database
echo -e "${BLUE}Initializing database...${NC}"
docker-compose exec -T api python -c "from app.core.database import init_db; init_db()" || true

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Services are now running:"
echo "  🔵 API Server:  http://localhost:8000"
echo "  🎨 Frontend:    http://localhost:3000"
echo "  🐘 PostgreSQL:  localhost:5432"
echo "  ♻️  Redis:       localhost:6379"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop services: docker-compose down"
echo ""
