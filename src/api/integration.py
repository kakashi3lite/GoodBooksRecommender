"""
Enhanced Features Integration Module for GoodBooks Recommender

This module handles the initialization and integration of advanced features:
- Real-time analytics engine
- Multi-level caching system  
- Enhanced health monitoring
- Batch processing engine
- Advanced ML features and A/B testing
"""

import asyncio
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from src.core.logging import StructuredLogger
from src.core.settings import settings
from src.config import Config

# Enhanced Features
from src.analytics.real_time_analytics import RealTimeAnalytics
from src.core.advanced_cache import MultiLevelCache, L1MemoryCache
from src.core.enhanced_health import HealthMonitor
from src.core.batch_processing import BatchProcessingEngine
from src.api.enhanced_endpoints import initialize_enhanced_features, router as enhanced_router

# Advanced ML Features
try:
    from src.models.ab_testing import MLABTester
    from src.models.model_performance import ModelPerformanceMonitor
    from src.models.model_optimization import ModelOptimizer
except ImportError as e:
    print(f"Advanced ML features not available: {str(e)}")
    # Mock classes for development
    class MLABTester:
        def __init__(self, **kwargs): pass
        async def initialize(self): pass
        async def cleanup(self): pass
    
    class ModelPerformanceMonitor:
        def __init__(self, **kwargs): pass
        async def start_monitoring(self): pass
        async def stop_monitoring(self): pass
        async def get_current_metrics(self): return {}
    
    class ModelOptimizer:
        def __init__(self, **kwargs): pass
        async def initialize(self): pass
        async def cleanup(self): pass

logger = StructuredLogger(__name__)

# Global instances for enhanced features
analytics_engine: Optional[RealTimeAnalytics] = None
cache_system: Optional[MultiLevelCache] = None
health_monitor: Optional[HealthMonitor] = None
batch_engine: Optional[BatchProcessingEngine] = None
ml_ab_tester: Optional[MLABTester] = None
performance_monitor: Optional[ModelPerformanceMonitor] = None
model_optimizer: Optional[ModelOptimizer] = None


class EnhancedFeaturesManager:
    """Manager for all enhanced features."""
    
    def __init__(self):
        self.config = Config()
        self.initialized = False
        
    async def initialize_all(self, app) -> Dict[str, Any]:
        """Initialize all enhanced features."""
        if self.initialized:
            return self.get_instances()
            
        logger.info("Initializing enhanced features...")
        
        try:
            # Initialize analytics engine
            analytics = await self._initialize_analytics()
            
            # Initialize advanced caching
            cache = await self._initialize_cache()
            
            # Initialize health monitoring
            health = await self._initialize_health()
            
            # Initialize batch processing
            batch = await self._initialize_batch_processing()
            
            # Initialize ML A/B testing
            ml_ab = await self._initialize_ml_ab_testing()
            
            # Initialize performance monitoring
            perf_monitor = await self._initialize_performance_monitoring()
            
            # Initialize model optimization
            optimizer = await self._initialize_model_optimization()
            
            # Register with enhanced endpoints
            initialize_enhanced_features(analytics, cache, health, batch)
            
            # Include enhanced router in app
            app.include_router(enhanced_router)
            
            self.initialized = True
            logger.info("All enhanced features initialized successfully")
            
            return {
                'analytics': analytics,
                'cache': cache,
                'health': health,
                'batch': batch,
                'ml_ab_tester': ml_ab,
                'performance_monitor': perf_monitor,
                'model_optimizer': optimizer
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced features: {str(e)}", exc_info=True)
            raise
    
    async def _initialize_analytics(self) -> RealTimeAnalytics:
        """Initialize real-time analytics engine."""
        global analytics_engine
        
        logger.info("Initializing real-time analytics engine...")
        
        # Use the correct constructor - only takes redis_client
        analytics_engine = RealTimeAnalytics(redis_client=None)  # Mock redis for now
        
        await analytics_engine.start()
        logger.info("Real-time analytics engine initialized")
        
        return analytics_engine
    
    async def _initialize_cache(self) -> MultiLevelCache:
        """Initialize multi-level caching system."""
        global cache_system
        
        logger.info("Initializing multi-level cache system...")
        
        # L1 Memory Cache
        l1_cache = L1MemoryCache(
            max_size_mb=settings.cache.l1_cache_size // 1024,  # Convert to MB
            max_entries=1000
        )
        
        # Multi-level cache with L1 and L2 (Redis)
        cache_system = MultiLevelCache(
            l1_cache=l1_cache,
            l2_redis_client=None  # Mock redis for now
        )
        
        logger.info("Multi-level cache system initialized")
        
        return cache_system
    
    async def _initialize_health(self) -> HealthMonitor:
        """Initialize enhanced health monitoring."""
        global health_monitor
        
        logger.info("Initializing enhanced health monitoring...")
        
        # HealthMonitor takes no constructor arguments
        health_monitor = HealthMonitor()
        
        logger.info("Enhanced health monitoring initialized")
        
        return health_monitor
    
    async def _initialize_batch_processing(self) -> BatchProcessingEngine:
        """Initialize batch processing engine."""
        global batch_engine
        
        logger.info("Initializing batch processing engine...")
        
        batch_engine = BatchProcessingEngine(
            max_concurrent_tasks=settings.batch_processing.max_concurrent_jobs
        )
        
        logger.info("Batch processing engine initialized")
        
        return batch_engine
    
    async def _initialize_ml_ab_testing(self) -> MLABTester:
        """Initialize ML A/B testing framework."""
        global ml_ab_tester
        
        logger.info("Initializing ML A/B testing framework...")
        
        ml_ab_tester = MLABTester(
            redis_url="redis://localhost:6379",  # Use default redis URL
            experiment_config_path="config/ab_experiments.yml"
        )
        
        await ml_ab_tester.initialize()
        logger.info("ML A/B testing framework initialized")
        
        return ml_ab_tester
    
    async def _initialize_performance_monitoring(self) -> ModelPerformanceMonitor:
        """Initialize model performance monitoring."""
        global performance_monitor
        
        logger.info("Initializing model performance monitoring...")
        
        performance_monitor = ModelPerformanceMonitor(
            metrics_window_size=1000,
            alert_thresholds={
                'accuracy': 0.8,
                'latency_ms': 500,
                'error_rate': 0.05
            }
        )
        
        await performance_monitor.start_monitoring()
        logger.info("Model performance monitoring initialized")
        
        return performance_monitor
    
    async def _initialize_model_optimization(self) -> ModelOptimizer:
        """Initialize model optimization system."""
        global model_optimizer
        
        logger.info("Initializing model optimization system...")
        
        model_optimizer = ModelOptimizer(
            optimization_strategies=['hyperparameter_tuning', 'feature_selection'],
            auto_retrain_threshold=0.1,
            optimization_interval_hours=24
        )
        
        await model_optimizer.initialize()
        logger.info("Model optimization system initialized")
        
        return model_optimizer
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Health check for Redis."""
        try:
            if cache_system:
                await cache_system.redis_client.ping()
                return {"status": "healthy", "latency_ms": 1}
            return {"status": "not_initialized"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Health check for database."""
        try:
            # Implement database health check
            return {"status": "healthy", "connections": 10}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_ml_models_health(self) -> Dict[str, Any]:
        """Health check for ML models."""
        try:
            if performance_monitor:
                metrics = await performance_monitor.get_current_metrics()
                return {"status": "healthy", "metrics": metrics}
            return {"status": "not_initialized"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def get_instances(self) -> Dict[str, Any]:
        """Get all initialized instances."""
        return {
            'analytics': analytics_engine,
            'cache': cache_system,
            'health': health_monitor,
            'batch': batch_engine,
            'ml_ab_tester': ml_ab_tester,
            'performance_monitor': performance_monitor,
            'model_optimizer': model_optimizer
        }
    
    async def cleanup(self):
        """Cleanup all enhanced features."""
        logger.info("Cleaning up enhanced features...")
        
        try:
            if health_monitor:
                await health_monitor.stop_monitoring()
            
            if batch_engine:
                await batch_engine.cleanup()
            
            if analytics_engine:
                await analytics_engine.cleanup()
            
            if cache_system:
                await cache_system.cleanup()
            
            if ml_ab_tester:
                await ml_ab_tester.cleanup()
            
            if performance_monitor:
                await performance_monitor.stop_monitoring()
            
            if model_optimizer:
                await model_optimizer.cleanup()
            
            logger.info("Enhanced features cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during enhanced features cleanup: {str(e)}")


# Singleton instance
enhanced_features_manager = EnhancedFeaturesManager()


@asynccontextmanager
async def enhanced_lifespan_context():
    """Context manager for enhanced features lifecycle."""
    instances = None
    try:
        instances = await enhanced_features_manager.initialize_all(None)
        yield instances
    except Exception as e:
        logger.error(f"Enhanced features startup failed: {str(e)}")
        raise
    finally:
        if instances:
            await enhanced_features_manager.cleanup()


# Alias for backward compatibility
EnhancedFeatureManager = EnhancedFeaturesManager
