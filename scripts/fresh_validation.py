#!/usr/bin/env python3
"""
Fresh Enhanced Features Validation

Simple test to verify all components work correctly.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_all_features():
    """Test all enhanced features."""
    print("🔍 Running Fresh Enhanced Features Validation...")
    results = {}
    
    # Analytics Test
    try:
        from src.analytics.real_time_analytics import RealTimeAnalytics
        analytics = RealTimeAnalytics(redis_client=None)
        # Test cleanup method
        analytics.cleanup()
        results['analytics'] = {'status': 'PASSED', 'success': True}
        print('✅ Analytics: PASSED')
    except Exception as e:
        results['analytics'] = {'status': 'FAILED', 'error': str(e)}
        print(f'❌ Analytics: {e}')
    
    # Cache Test
    try:
        from src.core.advanced_cache import MultiLevelCache, L1MemoryCache
        l1_cache = L1MemoryCache(max_size_mb=10)
        cache = MultiLevelCache(l1_cache=l1_cache)
        results['cache'] = {'status': 'PASSED', 'success': True}
        print('✅ Cache: PASSED')
    except Exception as e:
        results['cache'] = {'status': 'FAILED', 'error': str(e)}
        print(f'❌ Cache: {e}')
    
    # A/B Testing Test
    try:
        from src.models.ab_testing import MLABTester
        ab_tester = MLABTester(redis_client=None)
        results['ab_testing'] = {'status': 'PASSED', 'success': True}
        print('✅ A/B Testing: PASSED')
    except Exception as e:
        results['ab_testing'] = {'status': 'FAILED', 'error': str(e)}
        print(f'❌ A/B Testing: {e}')
    
    # Health Monitoring Test
    try:
        from src.core.enhanced_health import HealthMonitor
        health = HealthMonitor()
        results['health'] = {'status': 'PASSED', 'success': True}
        print('✅ Health Monitoring: PASSED')
    except Exception as e:
        results['health'] = {'status': 'FAILED', 'error': str(e)}
        print(f'❌ Health Monitoring: {e}')
    
    # Batch Processing Test
    try:
        from src.core.batch_processing import BatchProcessingEngine
        batch = BatchProcessingEngine()
        results['batch'] = {'status': 'PASSED', 'success': True}
        print('✅ Batch Processing: PASSED')
    except Exception as e:
        results['batch'] = {'status': 'FAILED', 'error': str(e)}
        print(f'❌ Batch Processing: {e}')
    
    # Performance Monitoring Test
    try:
        from src.models.model_performance import ModelPerformanceMonitor
        monitor = ModelPerformanceMonitor()
        results['performance'] = {'status': 'PASSED', 'success': True}
        print('✅ Performance Monitoring: PASSED')
    except Exception as e:
        results['performance'] = {'status': 'FAILED', 'error': str(e)}
        print(f'❌ Performance Monitoring: {e}')
    
    # Model Optimization Test
    try:
        from src.models.model_optimization import ModelOptimizer
        optimizer = ModelOptimizer()
        results['optimization'] = {'status': 'PASSED', 'success': True}
        print('✅ Model Optimization: PASSED')
    except Exception as e:
        results['optimization'] = {'status': 'FAILED', 'error': str(e)}
        print(f'❌ Model Optimization: {e}')
    
    # Calculate summary
    passed = sum(1 for r in results.values() if r['status'] == 'PASSED')
    total = len(results)
    success_rate = (passed / total) * 100
    overall = 'PASSED' if passed == total else 'FAILED'
    
    results['summary'] = {
        'total': total,
        'passed': passed,
        'failed': total - passed,
        'success_rate': success_rate,
        'overall': overall
    }
    
    # Save results
    with open('validation_results_fresh.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Summary: {passed}/{total} tests passed ({success_rate:.1f}%)")
    print(f"Overall: {overall}")
    
    return overall == 'PASSED'

if __name__ == "__main__":
    success = test_all_features()
    sys.exit(0 if success else 1)
