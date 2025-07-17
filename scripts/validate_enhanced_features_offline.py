#!/usr/bin/env python3
"""
Offline validation script for enhanced features.
This script validates the enhanced features without requiring external dependencies like Redis.
"""

import asyncio
import logging
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from src.analytics.real_time_analytics import (
        RealTimeAnalytics, UserInteraction, RecommendationEvent, RealTimeMetrics
    )
    from src.core.advanced_cache import L1MemoryCache, MultiLevelCache, CacheStats
    from src.core.enhanced_health import HealthMonitor, HealthStatus
    from src.core.batch_processing import BatchProcessingEngine
    from src.core.settings import Settings
except ImportError as e:
    print(f"Import error: {e}")
    print("Note: This validation requires the enhanced modules to be properly installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OfflineEnhancedFeaturesValidator:
    """Offline validator for enhanced features."""
    
    def __init__(self):
        self.results = {}
        self.settings = Settings()
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests."""
        logger.info("🚀 Starting Offline Enhanced Features Validation...")
        
        # Test modules individually
        test_cases = [
            ("analytics", self.validate_analytics_offline),
            ("cache", self.validate_cache_offline),
            ("health", self.validate_health_offline),
            ("batch_processing", self.validate_batch_processing_offline),
        ]
        
        for test_name, test_func in test_cases:
            logger.info(f"Validating {test_name}...")
            start_time = time.time()
            try:
                result = await test_func()
                duration = time.time() - start_time
                
                if result:
                    logger.info(f"Validation {test_name}: PASSED ({duration:.2f}s)")
                    self.results[test_name] = {
                        "status": "PASSED",
                        "duration": duration,
                        "result": result
                    }
                else:
                    logger.error(f"Validation {test_name}: FAILED ({duration:.2f}s)")
                    self.results[test_name] = {
                        "status": "FAILED",
                        "duration": duration,
                        "result": result
                    }
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Validation {test_name}: ERROR ({duration:.2f}s) - {str(e)}")
                self.results[test_name] = {
                    "status": "ERROR",
                    "duration": duration,
                    "error": str(e)
                }
        
        # Generate summary
        self.results["summary"] = self.generate_summary()
        
        logger.info("Offline validation completed")
        return self.results
    
    async def validate_analytics_offline(self) -> Dict[str, Any]:
        """Validate analytics functionality in offline mode."""
        try:
            # Test analytics classes can be instantiated
            analytics = RealTimeAnalytics(redis_client=None)
            
            # Test creating events
            interaction = UserInteraction(
                user_id="test_user",
                event_type="view",
                item_id="test_item"
            )
            
            event = RecommendationEvent(
                user_id="test_user",
                recommendation_type="collaborative",
                items_recommended=["item1", "item2"],
                response_time_ms=100.0,
                model_version="v1.0"
            )
            
            # Test metrics creation
            metrics = RealTimeMetrics(
                active_users_count=10,
                recommendations_per_minute=50,
                average_response_time_ms=120.0,
                model_prediction_accuracy=0.85,
                cache_hit_ratio=0.75
            )
            
            return {
                "analytics_created": True,
                "interaction_event_created": True,
                "recommendation_event_created": True,
                "metrics_created": True
            }
            
        except Exception as e:
            logger.error(f"Analytics offline validation failed: {str(e)}")
            return False
    
    async def validate_cache_offline(self) -> Dict[str, Any]:
        """Validate cache functionality in offline mode."""
        try:
            # Test L1 cache
            l1_cache = L1MemoryCache(max_size_mb=10)
            await l1_cache.set("test_key", "test_value", ttl=60)
            value = await l1_cache.get("test_key")
            
            # Test multi-level cache (without Redis)
            cache = MultiLevelCache(
                l1_cache=l1_cache,
                l2_redis_client=None
            )
            
            await cache.set("ml_test_key", "ml_test_value", l1_ttl=60, l2_ttl=60)
            ml_value = await cache.get("ml_test_key")
            
            # Test stats
            stats = await cache.get_comprehensive_stats()
            
            return {
                "l1_cache_working": value == "test_value",
                "multi_level_cache_working": ml_value == "ml_test_value",
                "stats_available": stats is not None
            }
            
        except Exception as e:
            logger.error(f"Cache offline validation failed: {str(e)}")
            return False
    
    async def validate_health_offline(self) -> Dict[str, Any]:
        """Validate health monitoring in offline mode."""
        try:
            # Test health monitor creation
            health_monitor = HealthMonitor()
            
            # Test health check (should work without external dependencies)
            report = await health_monitor.run_health_check()
            
            # Test health summary
            summary = health_monitor.get_health_summary()
            
            return {
                "health_monitor_created": True,
                "health_check_run": report is not None,
                "summary_available": summary is not None,
                "overall_status": report.overall_status.value if report else "unknown"
            }
            
        except Exception as e:
            logger.error(f"Health offline validation failed: {str(e)}")
            return False
    
    async def validate_batch_processing_offline(self) -> Dict[str, Any]:
        """Validate batch processing in offline mode."""
        try:
            # Test batch processing engine creation
            batch_engine = BatchProcessingEngine()
            
            # Create a test processor
            from src.core.batch_processing import BatchProcessor, BatchTask
            
            class TestProcessor(BatchProcessor):
                def get_processor_type(self) -> str:
                    return "test_job"
                
                async def process_task(self, task: BatchTask) -> Any:
                    return {"processed": True, "data": task.data}
            
            # Register the test processor
            test_processor = TestProcessor()
            batch_engine.register_processor(test_processor)
            
            # Test batch job submission (without execution)
            batch_id = await batch_engine.submit_batch_job(
                job_type="test_job",
                tasks_data=[{"test": "data1"}, {"test": "data2"}]
            )
            
            # Test job status
            status = await batch_engine.get_job_status(batch_id)
            
            # Test active jobs summary
            summary = await batch_engine.get_active_jobs_summary()
            
            return {
                "batch_engine_created": True,
                "processor_registered": True,
                "job_submitted": batch_id is not None,
                "status_accessible": status is not None,
                "summary_accessible": summary is not None
            }
            
        except Exception as e:
            logger.error(f"Batch processing offline validation failed: {str(e)}")
            return False
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate validation summary."""
        total_tests = len([k for k in self.results.keys() if k != "summary"])
        passed_tests = len([r for r in self.results.values() if isinstance(r, dict) and r.get("status") == "PASSED"])
        failed_tests = len([r for r in self.results.values() if isinstance(r, dict) and r.get("status") == "FAILED"])
        error_tests = len([r for r in self.results.values() if isinstance(r, dict) and r.get("status") == "ERROR"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        overall_status = "PASSED" if passed_tests == total_tests else "FAILED"
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "success_rate": round(success_rate, 1),
            "overall_status": overall_status
        }
    
    def print_results(self):
        """Print validation results in a formatted way."""
        print("\n" + "="*60)
        print("OFFLINE ENHANCED FEATURES VALIDATION RESULTS")
        print("="*60)
        
        for test_name, result in self.results.items():
            if test_name == "summary":
                continue
                
            status = result.get("status", "UNKNOWN")
            duration = result.get("duration", 0)
            
            status_emoji = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "💥"
            print(f"{status_emoji} {test_name:<20} {status:<8} ({duration:.2f}s)")
        
        print("-" * 60)
        summary = self.results.get("summary", {})
        print("SUMMARY:")
        print(f"  Total Tests: {summary.get('total_tests', 0)}")
        print(f"  Passed: {summary.get('passed', 0)}")
        print(f"  Failed: {summary.get('failed', 0)}")
        print(f"  Errors: {summary.get('errors', 0)}")
        print(f"  Success Rate: {summary.get('success_rate', 0)}%")
        print(f"  Overall Status: {summary.get('overall_status', 'UNKNOWN')}")
        print("="*60)
        
        return summary.get('overall_status') == 'PASSED'

async def main():
    """Main validation function."""
    validator = OfflineEnhancedFeaturesValidator()
    
    try:
        results = await validator.run_all_validations()
        success = validator.print_results()
        
        # Save results to file
        results_file = Path(__file__).parent.parent / "validation_results_offline.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📝 Detailed results saved to: {results_file}")
        
        if success:
            print("🎉 Offline validation passed!")
            return 0
        else:
            print("💥 Offline validation failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Validation failed with error: {str(e)}")
        print(f"💥 Validation failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
