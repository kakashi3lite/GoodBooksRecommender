#!/bin/bash

# Production startup script for GoodBooks Recommender
# Follows Bookworm AI Coding Standards for deployment

set -e

echo "🚀 Starting GoodBooks Recommender Production Deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Set Docker Compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# Check for environment file
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_warning "Please edit .env file with your production settings before continuing."
        print_warning "Pay special attention to:"
        print_warning "  - SECRET_KEY"
        print_warning "  - DATABASE credentials"
        print_warning "  - REDIS_PASSWORD"
        print_warning "  - API keys"
        read -p "Press Enter after updating .env file..."
    else
        print_error ".env.example not found. Cannot create .env file."
        exit 1
    fi
fi

# Parse command line arguments
ENVIRONMENT="production"
PROFILE=""
REBUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--profile)
            PROFILE="--profile $2"
            shift 2
            ;;
        --rebuild)
            REBUILD=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -e, --environment ENV    Set environment (development/production)"
            echo "  -p, --profile PROFILE    Docker Compose profile (monitoring/proxy)"
            echo "      --rebuild           Force rebuild of images"
            echo "  -h, --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Start production environment"
            echo "  $0 -e development                     # Start development environment"
            echo "  $0 -p monitoring                      # Start with monitoring stack"
            echo "  $0 -p monitoring --rebuild            # Rebuild and start with monitoring"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_status "Environment: $ENVIRONMENT"
if [ -n "$PROFILE" ]; then
    print_status "Profile: $PROFILE"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs data models monitoring/grafana/{dashboards,datasources} nginx/ssl scripts

# Set environment in .env file
if command -v sed &> /dev/null; then
    sed -i.bak "s/^ENVIRONMENT=.*/ENVIRONMENT=$ENVIRONMENT/" .env
    print_status "Updated ENVIRONMENT to $ENVIRONMENT in .env file"
fi

# Pull latest images
print_status "Pulling latest Docker images..."
$DOCKER_COMPOSE $PROFILE pull

# Build or rebuild images if needed
if [ "$REBUILD" = true ]; then
    print_status "Rebuilding Docker images..."
    $DOCKER_COMPOSE $PROFILE build --no-cache
else
    print_status "Building Docker images..."
    $DOCKER_COMPOSE $PROFILE build
fi

# Start services
print_status "Starting services..."
$DOCKER_COMPOSE $PROFILE up -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 10

# Check service status
print_status "Checking service status..."

# Check API health
if curl -f -s http://localhost:8000/health > /dev/null; then
    print_success "API is healthy ✓"
else
    print_error "API health check failed ✗"
fi

# Check Redis
if docker exec $(docker ps -q -f name=redis) redis-cli ping > /dev/null 2>&1; then
    print_success "Redis is healthy ✓"
else
    print_error "Redis health check failed ✗"
fi

# Check PostgreSQL
if docker exec $(docker ps -q -f name=postgres) pg_isready -U postgres > /dev/null 2>&1; then
    print_success "PostgreSQL is healthy ✓"
else
    print_error "PostgreSQL health check failed ✗"
fi

# Show running services
print_status "Running services:"
$DOCKER_COMPOSE ps

print_success "🎉 GoodBooks Recommender is now running!"
echo ""
print_status "Available endpoints:"
print_status "  📋 API Documentation: http://localhost:8000/docs"
print_status "  ❤️  Health Check: http://localhost:8000/health"
print_status "  📊 Metrics: http://localhost:8000/metrics"

if echo "$PROFILE" | grep -q "monitoring"; then
    print_status "  📈 Prometheus: http://localhost:9090"
    print_status "  📊 Grafana: http://localhost:3000 (admin/admin)"
fi

if echo "$PROFILE" | grep -q "proxy"; then
    print_status "  🌐 Nginx Proxy: http://localhost"
fi

echo ""
print_status "To view logs: $DOCKER_COMPOSE logs -f [service_name]"
print_status "To stop: $DOCKER_COMPOSE down"
print_status "To stop and remove volumes: $DOCKER_COMPOSE down -v"

# Show resource usage
echo ""
print_status "Resource usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
