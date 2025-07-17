#!/usr/bin/env python3
"""
Test Enhanced Features with New Pydantic Settings

This script tests all enhanced features using the new settings system.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_settings_import():
    """Test importing the new settings."""
    try:
        from src.core.settings import settings
        print("✓ Successfully imported settings")
        print(f"  - Environment: {settings.environment}")
        print(f"  - Debug: {settings.debug}")
        print(f"  - Cache enabled: {settings.cache.enable_multi_level}")
        print(f"  - Analytics enabled: {settings.analytics.enabled}")
        print(f"  - Batch processing enabled: {settings.batch_processing.enabled}")
        return True
    except Exception as e:
        print(f"✗ Failed to import settings: {e}")
        return False

def test_enhanced_modules():
    """Test importing all enhanced modules."""
    modules_to_test = [
        ('src.analytics.real_time_analytics', 'RealTimeAnalytics'),
        ('src.core.advanced_cache', 'MultiLevelCache'),
        ('src.core.enhanced_health', 'EnhancedHealthChecker'),
        ('src.core.batch_processing', 'BatchProcessor'),
        ('src.models.ab_testing', 'ABTestingFramework'),
        ('src.models.model_performance', 'ModelPerformanceMonitor'),
        ('src.models.model_optimization', 'ModelOptimizer'),
        ('src.api.enhanced_endpoints', 'None'),  # No main class
        ('src.api.integration', 'EnhancedFeatureManager'),
    ]
    
    success_count = 0
    total_count = len(modules_to_test)
    
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name] if class_name != 'None' else [])
            if class_name != 'None':
                cls = getattr(module, class_name)
                print(f"✓ Successfully imported {module_name}.{class_name}")
            else:
                print(f"✓ Successfully imported {module_name}")
            success_count += 1
        except Exception as e:
            print(f"✗ Failed to import {module_name}: {e}")
    
    print(f"\nModule Import Results: {success_count}/{total_count} successful")
    return success_count == total_count

def test_enhanced_feature_manager():
    """Test creating the enhanced feature manager with settings."""
    try:
        from src.core.settings import settings
        from src.api.integration import EnhancedFeatureManager
        
        # Create manager (no config parameter needed)
        manager = EnhancedFeatureManager()
        print("✓ Successfully created EnhancedFeatureManager")
        return True
    except Exception as e:
        print(f"✗ Failed to create EnhancedFeatureManager: {e}")
        return False

def test_individual_components():
    """Test creating individual components with settings."""
    from src.core.settings import settings
    
    tests = []
    
    # Test analytics
    try:
        from src.analytics.real_time_analytics import RealTimeAnalytics
        analytics = RealTimeAnalytics(redis_client=None)  # Mock redis client
        print("✓ Successfully created RealTimeAnalytics")
        tests.append(True)
    except Exception as e:
        print(f"✗ Failed to create RealTimeAnalytics: {e}")
        tests.append(False)
    
    # Test advanced cache
    try:
        from src.core.advanced_cache import L1MemoryCache, MultiLevelCache
        l1_cache = L1MemoryCache(max_size_mb=settings.cache.l1_cache_size // 1024)  # Convert to MB
        cache = MultiLevelCache(l1_cache=l1_cache)
        print("✓ Successfully created MultiLevelCache")
        tests.append(True)
    except Exception as e:
        print(f"✗ Failed to create MultiLevelCache: {e}")
        tests.append(False)
    
    # Test enhanced health checker
    try:
        from src.core.enhanced_health import EnhancedHealthChecker
        health = EnhancedHealthChecker()
        print("✓ Successfully created EnhancedHealthChecker")
        tests.append(True)
    except Exception as e:
        print(f"✗ Failed to create EnhancedHealthChecker: {e}")
        tests.append(False)
    
    # Test batch processor
    try:
        from src.core.batch_processing import BatchProcessor
        batch = BatchProcessor(
            max_concurrent_tasks=settings.batch_processing.max_concurrent_jobs
        )
        print("✓ Successfully created BatchProcessor")
        tests.append(True)
    except Exception as e:
        print(f"✗ Failed to create BatchProcessor: {e}")
        tests.append(False)
    
    return all(tests)

def main():
    """Main test function."""
    print("Testing Enhanced Features with New Settings")
    print("=" * 50)
    
    # Test settings import
    print("\n1. Testing Settings Import:")
    settings_ok = test_settings_import()
    
    # Test module imports
    print("\n2. Testing Module Imports:")
    imports_ok = test_enhanced_modules()
    
    # Test feature manager
    print("\n3. Testing Enhanced Feature Manager:")
    manager_ok = test_enhanced_feature_manager()
    
    # Test individual components
    print("\n4. Testing Individual Components:")
    components_ok = test_individual_components()
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Settings Import: {'✓' if settings_ok else '✗'}")
    print(f"Module Imports: {'✓' if imports_ok else '✗'}")
    print(f"Feature Manager: {'✓' if manager_ok else '✗'}")
    print(f"Individual Components: {'✓' if components_ok else '✗'}")
    
    all_passed = settings_ok and imports_ok and manager_ok and components_ok
    print(f"\nOverall Result: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
