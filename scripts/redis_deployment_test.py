#!/usr/bin/env python3
"""
Redis Deployment Readiness Script for GoodBooks Recommender

This script ensures Redis is properly configured and ready for deployment
with all enhanced features working correctly.
"""

import sys
import asyncio
import json
import time
import subprocess
import platform
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.logging import StructuredLogger
from src.analytics.real_time_analytics import RealTimeAnalytics
from src.models.ab_testing import MLABTester

logger = StructuredLogger(__name__)


class RedisDeploymentManager:
    """Manages Redis deployment and configuration for production readiness."""
    
    def __init__(self):
        self.redis_url = "redis://localhost:6379"
        self.redis_processes = []
        self.test_results = {}
    
    def check_redis_installation(self) -> bool:
        """Check if Redis is installed on the system or available via Docker."""
        # First check for Docker Redis container
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=goodbooks-redis", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "goodbooks-redis" in result.stdout:
                logger.info("✅ Redis available via Docker container (goodbooks-redis)")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Check for direct Redis installation
        try:
            # Try to find Redis executable
            result = subprocess.run(
                ["redis-server", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"Redis server found: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Try alternative locations
        redis_paths = [
            "redis-server",
            "/usr/local/bin/redis-server",
            "/usr/bin/redis-server",
            "C:\\Program Files\\Redis\\redis-server.exe"
        ]
        
        for redis_path in redis_paths:
            try:
                result = subprocess.run(
                    [redis_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"Redis server found at {redis_path}: {result.stdout.strip()}")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        return False
    
    def install_redis_guidance(self) -> str:
        """Provide installation guidance for Redis based on the platform."""
        os_name = platform.system().lower()
        
        if os_name == "windows":
            return '''
Redis Installation for Windows:
1. Easy Docker Setup: python scripts/setup_redis_docker.py
2. Manual Docker: docker run -d -p 6379:6379 --name goodbooks-redis redis:latest
3. Download Redis: https://github.com/tporadowski/redis/releases
4. Or use WSL2 with Ubuntu and install Redis there
'''
        elif os_name == "darwin":  # macOS
            return '''
Redis Installation for macOS:
1. Using Homebrew: brew install redis
2. Start Redis: brew services start redis
3. Or use Docker: docker run -d -p 6379:6379 redis:latest
'''
        else:  # Linux
            return '''
Redis Installation for Linux:
1. Ubuntu/Debian: sudo apt-get install redis-server
2. CentOS/RHEL: sudo yum install redis
3. Start Redis: sudo systemctl start redis
4. Or use Docker: docker run -d -p 6379:6379 redis:latest
'''
    
    def start_redis_server(self) -> bool:
        """Attempt to start Redis server if not running."""
        try:
            # Try to start Redis using common commands
            commands = [
                ["redis-server"],
                ["redis-server", "--daemonize", "yes"],
                ["/usr/local/bin/redis-server"],
                ["systemctl", "start", "redis"],
                ["service", "redis", "start"]
            ]
            
            for cmd in commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        logger.info(f"Redis server started with command: {' '.join(cmd)}")
                        time.sleep(2)  # Give Redis time to start
                        return True
                except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to start Redis server: {str(e)}")
            return False
    
    async def test_redis_connection(self) -> Dict[str, Any]:
        """Test Redis connection and basic operations."""
        try:
            import redis.asyncio as redis
            
            # Create Redis client
            client = redis.from_url(self.redis_url)
            
            # Test basic operations
            await client.ping()
            await client.set("test_key", "test_value", ex=60)
            value = await client.get("test_key")
            await client.delete("test_key")
            await client.close()
            
            return {
                "success": True,
                "connection": True,
                "basic_operations": True,
                "value_retrieved": value.decode() == "test_value" if value else False
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "connection": False
            }
    
    async def test_analytics_with_redis(self) -> Dict[str, Any]:
        """Test real-time analytics with Redis."""
        try:
            import redis.asyncio as redis
            
            # Create Redis client
            redis_client = redis.from_url(self.redis_url)
            await redis_client.ping()
            
            # Create analytics instance with Redis client
            analytics = RealTimeAnalytics(redis_client=redis_client)
            
            # Test user interaction tracking
            from src.analytics.real_time_analytics import UserInteraction
            interaction = UserInteraction(
                user_id="test_user_123",
                event_type="view",
                item_id="book_456",
                session_id="session_789"
            )
            
            await analytics.track_user_interaction(interaction)
            
            # Test metrics collection
            metrics = await analytics.get_current_metrics()
            
            # Cleanup
            await analytics.cleanup()
            await redis_client.close()
            
            return {
                "success": True,
                "tracking": True,
                "metrics": metrics is not None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
            
            # Test cleanup
            await analytics.cleanup()
            
            return {
                "success": True,
                "interaction_tracked": True,
                "metrics_collected": metrics is not None,
                "cleanup_successful": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_ab_testing_with_redis(self) -> Dict[str, Any]:
        """Test ML A/B testing with Redis."""
        try:
            import redis.asyncio as redis
            
            # Create Redis client
            redis_client = redis.from_url(self.redis_url)
            await redis_client.ping()
            
            # Create A/B tester with Redis client
            ab_tester = MLABTester(redis_url=self.redis_url, redis_client=redis_client)
            await ab_tester.initialize()
            
            # Simple test without creating complex experiment
            variant = await ab_tester.get_variant_for_user("test_user", "test_experiment")
            
            # Cleanup
            await ab_tester.cleanup()
            await redis_client.close()
            
            return {
                "success": True,
                "ab_testing_working": True,
                "variant_assignment": variant is not None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_comprehensive_redis_tests(self) -> Dict[str, Any]:
        """Run comprehensive Redis functionality tests."""
        logger.info("Starting comprehensive Redis deployment tests...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "redis_installation": {
                "installed": self.check_redis_installation(),
                "guidance": self.install_redis_guidance()
            }
        }
        
        # If Redis not installed, provide guidance
        if not results["redis_installation"]["installed"]:
            logger.warning("Redis not found. Please install Redis first.")
            print("\n❌ Redis not installed!")
            print(results["redis_installation"]["guidance"])
            return results
        
        # Try to start Redis if not running
        logger.info("Attempting to start Redis server...")
        redis_started = self.start_redis_server()
        
        # Test Redis connection
        logger.info("Testing Redis connection...")
        connection_test = await self.test_redis_connection()
        results["redis_connection"] = connection_test
        
        if not connection_test["success"]:
            logger.error("Redis connection failed. Please ensure Redis is running.")
            print(f"\n❌ Redis connection failed: {connection_test.get('error', 'Unknown error')}")
            print("\nTry starting Redis manually:")
            print("  - Windows: redis-server")
            print("  - macOS/Linux: redis-server or sudo systemctl start redis")
            print("  - Docker: docker run -d -p 6379:6379 redis:latest")
            return results
        
        # Test analytics with Redis
        logger.info("Testing real-time analytics with Redis...")
        analytics_test = await self.test_analytics_with_redis()
        results["analytics_redis"] = analytics_test
        
        # Test A/B testing with Redis
        logger.info("Testing ML A/B testing with Redis...")
        ab_test = await self.test_ab_testing_with_redis()
        results["ab_testing_redis"] = ab_test
        
        # Calculate overall success
        all_tests = [connection_test, analytics_test, ab_test]
        success_count = sum(1 for test in all_tests if test.get("success", False))
        results["summary"] = {
            "total_tests": len(all_tests),
            "passed": success_count,
            "failed": len(all_tests) - success_count,
            "success_rate": (success_count / len(all_tests)) * 100,
            "overall_status": "PASSED" if success_count == len(all_tests) else "FAILED"
        }
        
        return results
    
    def print_results(self, results: Dict[str, Any]):
        """Print comprehensive test results."""
        print("\n" + "=" * 80)
        print("🚀 REDIS DEPLOYMENT READINESS REPORT")
        print("=" * 80)
        
        # Redis installation status
        installation = results.get("redis_installation", {})
        if installation.get("installed", False):
            print("✅ Redis Installation        FOUND")
        else:
            print("❌ Redis Installation        NOT FOUND")
            print(installation.get("guidance", ""))
            return
        
        # Connection test
        connection = results.get("redis_connection", {})
        if connection.get("success", False):
            print("✅ Redis Connection          SUCCESS")
            print("✅ Basic Operations          SUCCESS")
        else:
            print(f"❌ Redis Connection          FAILED - {connection.get('error', 'Unknown')}")
        
        # Analytics test
        analytics = results.get("analytics_redis", {})
        if analytics.get("success", False):
            print("✅ Analytics with Redis      SUCCESS")
        else:
            print(f"❌ Analytics with Redis      FAILED - {analytics.get('error', 'Unknown')}")
        
        # A/B testing test
        ab_testing = results.get("ab_testing_redis", {})
        if ab_testing.get("success", False):
            print("✅ A/B Testing with Redis    SUCCESS")
        else:
            print(f"❌ A/B Testing with Redis    FAILED - {ab_testing.get('error', 'Unknown')}")
        
        # Summary
        summary = results.get("summary", {})
        print("-" * 80)
        print("📊 SUMMARY:")
        print(f"   Total Tests: {summary.get('total_tests', 0)}")
        print(f"   Passed: {summary.get('passed', 0)}")
        print(f"   Failed: {summary.get('failed', 0)}")
        print(f"   Success Rate: {summary.get('success_rate', 0):.1f}%")
        print(f"   Overall Status: {summary.get('overall_status', 'UNKNOWN')}")
        print("=" * 80)
        
        if summary.get("overall_status") == "PASSED":
            print("\n🎉 REDIS DEPLOYMENT READY!")
            print("✨ All Redis-dependent features are working correctly!")
            print("🚀 System is ready for production deployment with Redis!")
        else:
            print("\n💥 Redis deployment needs attention")
            print("🔧 Please resolve the issues above before deployment")


async def main():
    """Main function for Redis deployment readiness."""
    manager = RedisDeploymentManager()
    
    try:
        results = await manager.run_comprehensive_redis_tests()
        manager.print_results(results)
        
        # Save results
        results_file = project_root / "redis_deployment_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📝 Results saved to: {results_file}")
        
        # Return appropriate exit code
        overall_status = results.get("summary", {}).get("overall_status")
        return 0 if overall_status == "PASSED" else 1
        
    except Exception as e:
        logger.error(f"Redis deployment test failed: {str(e)}")
        print(f"\n💥 Redis deployment test failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
