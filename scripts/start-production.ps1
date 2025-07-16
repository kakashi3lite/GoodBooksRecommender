# Production startup script for GoodBooks Recommender (Windows PowerShell)
# Follows Bookworm AI Coding Standards for deployment

param(
    [string]$Environment = "production",
    [string]$Profile = "",
    [switch]$Rebuild = $false,
    [switch]$Help = $false
)

# Function to print colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    
    switch ($Type) {
        "Info" { Write-Host "[INFO] $Message" -ForegroundColor Blue }
        "Success" { Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
        "Warning" { Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
        "Error" { Write-Host "[ERROR] $Message" -ForegroundColor Red }
        default { Write-Host "$Message" }
    }
}

# Show help
if ($Help) {
    Write-Host "GoodBooks Recommender Production Startup Script"
    Write-Host ""
    Write-Host "USAGE:"
    Write-Host "  .\scripts\start-production.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "OPTIONS:"
    Write-Host "  -Environment ENV      Set environment (development/production)"
    Write-Host "  -Profile PROFILE      Docker Compose profile (monitoring/proxy)"
    Write-Host "  -Rebuild              Force rebuild of images"
    Write-Host "  -Help                 Show this help message"
    Write-Host ""
    Write-Host "EXAMPLES:"
    Write-Host "  .\scripts\start-production.ps1"
    Write-Host "  .\scripts\start-production.ps1 -Environment development"
    Write-Host "  .\scripts\start-production.ps1 -Profile monitoring"
    Write-Host "  .\scripts\start-production.ps1 -Profile monitoring -Rebuild"
    exit 0
}

Write-ColorOutput "🚀 Starting GoodBooks Recommender Production Deployment" "Info"

# Check if Docker is installed and running
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-ColorOutput "Docker is not installed. Please install Docker Desktop first." "Error"
    exit 1
}

try {
    docker info | Out-Null
} catch {
    Write-ColorOutput "Docker is not running. Please start Docker Desktop first." "Error"
    exit 1
}

# Check if Docker Compose is available
$dockerComposeCmd = ""
if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    $dockerComposeCmd = "docker-compose"
} elseif (docker compose version -ErrorAction SilentlyContinue) {
    $dockerComposeCmd = "docker compose"
} else {
    Write-ColorOutput "Docker Compose is not available. Please install Docker Compose." "Error"
    exit 1
}

# Check for environment file
if (-not (Test-Path ".env")) {
    Write-ColorOutput ".env file not found." "Warning"
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-ColorOutput "Created .env from .env.example" "Info"
        Write-ColorOutput "Please edit .env file with your production settings before continuing." "Warning"
        Write-ColorOutput "Pay special attention to:" "Warning"
        Write-ColorOutput "  - SECRET_KEY" "Warning"
        Write-ColorOutput "  - DATABASE credentials" "Warning"
        Write-ColorOutput "  - REDIS_PASSWORD" "Warning"
        Write-ColorOutput "  - API keys" "Warning"
        Read-Host "Press Enter after updating .env file"
    } else {
        Write-ColorOutput ".env.example not found. Cannot create .env file." "Error"
        exit 1
    }
}

Write-ColorOutput "Environment: $Environment" "Info"
if ($Profile) {
    Write-ColorOutput "Profile: $Profile" "Info"
}

# Create necessary directories
Write-ColorOutput "Creating necessary directories..." "Info"
$directories = @("logs", "data", "models", "monitoring\grafana\dashboards", "monitoring\grafana\datasources", "nginx\ssl", "scripts")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Update environment in .env file
if (Test-Path ".env") {
    $envContent = Get-Content ".env"
    $envContent = $envContent -replace "^ENVIRONMENT=.*", "ENVIRONMENT=$Environment"
    $envContent | Set-Content ".env"
    Write-ColorOutput "Updated ENVIRONMENT to $Environment in .env file" "Info"
}

# Build Docker Compose command
$composeArgs = @()
if ($Profile) {
    $composeArgs += "--profile", $Profile
}

# Pull latest images
Write-ColorOutput "Pulling latest Docker images..." "Info"
& $dockerComposeCmd @composeArgs pull

# Build or rebuild images
if ($Rebuild) {
    Write-ColorOutput "Rebuilding Docker images..." "Info"
    & $dockerComposeCmd @composeArgs build --no-cache
} else {
    Write-ColorOutput "Building Docker images..." "Info"
    & $dockerComposeCmd @composeArgs build
}

# Start services
Write-ColorOutput "Starting services..." "Info"
& $dockerComposeCmd @composeArgs up -d

# Wait for services to be healthy
Write-ColorOutput "Waiting for services to be healthy..." "Info"
Start-Sleep -Seconds 10

# Check service status
Write-ColorOutput "Checking service status..." "Info"

# Check API health
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-ColorOutput "API is healthy ✓" "Success"
    } else {
        Write-ColorOutput "API health check failed ✗" "Error"
    }
} catch {
    Write-ColorOutput "API health check failed ✗" "Error"
}

# Check Redis
try {
    $redisContainer = docker ps -q -f name=redis
    if ($redisContainer) {
        docker exec $redisContainer redis-cli ping | Out-Null
        Write-ColorOutput "Redis is healthy ✓" "Success"
    } else {
        Write-ColorOutput "Redis container not found ✗" "Error"
    }
} catch {
    Write-ColorOutput "Redis health check failed ✗" "Error"
}

# Check PostgreSQL
try {
    $postgresContainer = docker ps -q -f name=postgres
    if ($postgresContainer) {
        docker exec $postgresContainer pg_isready -U postgres | Out-Null
        Write-ColorOutput "PostgreSQL is healthy ✓" "Success"
    } else {
        Write-ColorOutput "PostgreSQL container not found ✗" "Error"
    }
} catch {
    Write-ColorOutput "PostgreSQL health check failed ✗" "Error"
}

# Show running services
Write-ColorOutput "Running services:" "Info"
& $dockerComposeCmd ps

Write-ColorOutput "🎉 GoodBooks Recommender is now running!" "Success"
Write-Host ""
Write-ColorOutput "Available endpoints:" "Info"
Write-ColorOutput "  📋 API Documentation: http://localhost:8000/docs" "Info"
Write-ColorOutput "  ❤️  Health Check: http://localhost:8000/health" "Info"
Write-ColorOutput "  📊 Metrics: http://localhost:8000/metrics" "Info"

if ($Profile -eq "monitoring") {
    Write-ColorOutput "  📈 Prometheus: http://localhost:9090" "Info"
    Write-ColorOutput "  📊 Grafana: http://localhost:3000 (admin/admin)" "Info"
}

if ($Profile -eq "proxy") {
    Write-ColorOutput "  🌐 Nginx Proxy: http://localhost" "Info"
}

Write-Host ""
Write-ColorOutput "To view logs: $dockerComposeCmd logs -f [service_name]" "Info"
Write-ColorOutput "To stop: $dockerComposeCmd down" "Info"
Write-ColorOutput "To stop and remove volumes: $dockerComposeCmd down -v" "Info"

# Show resource usage
Write-Host ""
Write-ColorOutput "Resource usage:" "Info"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
