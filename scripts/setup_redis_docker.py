#!/usr/bin/env python3
"""
Quick Redis Setup Script using Docker

This script sets up Redis using Docker for the GoodBooks Recommender project.
"""

import subprocess
import sys
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.logging import StructuredLogger

logger = StructuredLogger(__name__)


def check_docker():
    """Check if Docker is available."""
    try:
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True, check=True)
        logger.info(f"Docker available: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Docker not found. Please install Docker Desktop.")
        return False


def check_redis_running():
    """Check if Redis container is already running."""
    try:
        result = subprocess.run(["docker", "ps", "--filter", "name=goodbooks-redis", "--format", "{{.Names}}"],
                              capture_output=True, text=True, check=True)
        return "goodbooks-redis" in result.stdout
    except subprocess.CalledProcessError:
        return False


def start_redis_container():
    """Start Redis container for GoodBooks Recommender."""
    logger.info("Starting Redis container...")
    
    try:
        # Stop and remove existing container if any
        subprocess.run(["docker", "stop", "goodbooks-redis"], 
                      capture_output=True, check=False)
        subprocess.run(["docker", "rm", "goodbooks-redis"], 
                      capture_output=True, check=False)
        
        # Start new Redis container
        cmd = [
            "docker", "run", "-d",
            "--name", "goodbooks-redis",
            "-p", "6379:6379",
            "--restart", "unless-stopped",
            "redis:7-alpine",
            "redis-server",
            "--appendonly", "yes",
            "--maxmemory", "256mb",
            "--maxmemory-policy", "allkeys-lru"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        container_id = result.stdout.strip()
        
        logger.info(f"Redis container started: {container_id[:12]}")
        
        # Wait for Redis to be ready
        logger.info("Waiting for Redis to be ready...")
        for i in range(30):
            try:
                test_result = subprocess.run(
                    ["docker", "exec", "goodbooks-redis", "redis-cli", "ping"],
                    capture_output=True, text=True, check=True
                )
                if "PONG" in test_result.stdout:
                    logger.info("Redis is ready!")
                    return True
            except subprocess.CalledProcessError:
                pass
            
            time.sleep(1)
        
        logger.error("Redis failed to start within 30 seconds")
        return False
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Redis container: {e.stderr}")
        return False


def test_redis_connection():
    """Test Redis connection from Python."""
    logger.info("Testing Redis connection from Python...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Test basic operations
        r.set('test_key', 'test_value', ex=10)
        value = r.get('test_key')
        
        if value == 'test_value':
            logger.info("✅ Redis connection test successful!")
            
            # Set up initial keys for GoodBooks features
            feature_keys = {
                'analytics:initialized': 'true',
                'cache:initialized': 'true',
                'health:initialized': 'true',
                'batch:initialized': 'true',
                'ab_testing:initialized': 'true',
                'performance:initialized': 'true',
                'optimization:initialized': 'true'
            }
            
            for key, value in feature_keys.items():
                r.set(key, value, ex=3600)  # 1 hour expiry
                
            logger.info("✅ GoodBooks feature keys initialized!")
            
            # Clean up test key
            r.delete('test_key')
            return True
        else:
            logger.error("❌ Redis connection test failed!")
            return False
            
    except ImportError:
        logger.error("Redis Python package not installed. Run: pip install redis")
        return False
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {str(e)}")
        return False


def create_docker_compose_override():
    """Create docker-compose override for development."""
    logger.info("Creating docker-compose.override.yml for development...")
    
    override_content = """version: '3.8'

services:
  redis:
    ports:
      - "6379:6379"
    environment:
      - REDIS_PASSWORD=
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  redis-data:
    driver: local
"""
    
    override_file = project_root / "docker-compose.override.yml"
    with open(override_file, 'w') as f:
        f.write(override_content)
    
    logger.info(f"Created {override_file}")


def print_redis_info():
    """Print Redis connection information."""
    print("\n" + "="*60)
    print("🚀 REDIS SETUP COMPLETE")
    print("="*60)
    print("Redis is now running and ready for GoodBooks Recommender!")
    print()
    print("Connection Details:")
    print("  Host: localhost")
    print("  Port: 6379")
    print("  Password: (none)")
    print()
    print("Container Management:")
    print("  View logs:    docker logs goodbooks-redis")
    print("  Stop Redis:   docker stop goodbooks-redis")
    print("  Start Redis:  docker start goodbooks-redis")
    print("  Remove:       docker rm -f goodbooks-redis")
    print()
    print("Redis CLI Access:")
    print("  docker exec -it goodbooks-redis redis-cli")
    print()
    print("Next Steps:")
    print("  1. Run validation: python scripts/validate_enhanced_features_final.py")
    print("  2. Deploy features: python scripts/deploy_enhanced_features.py")
    print("  3. Start application: python -m uvicorn src.api.main:app --reload")
    print("="*60)


def main():
    """Main setup function."""
    print("🔧 Setting up Redis for GoodBooks Recommender...")
    
    # Check prerequisites
    if not check_docker():
        print("❌ Docker is required but not available.")
        print("Please install Docker Desktop and try again.")
        return False
    
    # Check if Redis is already running
    if check_redis_running():
        logger.info("Redis container is already running")
        if test_redis_connection():
            print_redis_info()
            return True
        else:
            logger.warning("Redis container running but connection failed, restarting...")
    
    # Start Redis container
    if not start_redis_container():
        print("❌ Failed to start Redis container")
        return False
    
    # Test connection
    if not test_redis_connection():
        print("❌ Redis connection test failed")
        return False
    
    # Create development override
    create_docker_compose_override()
    
    # Print success information
    print_redis_info()
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        sys.exit(1)
