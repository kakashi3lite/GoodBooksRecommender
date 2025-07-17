"""
Integration Tests for Enhanced Features

This module provides comprehensive tests for all enhanced features including:
- Real-time analytics
- Advanced caching
- Enhanced health monitoring
- Batch processing
- ML A/B testing
- Model performance monitoring
- Model optimization
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from src.analytics.real_time_analytics import RealTimeAnalytics, UserInteraction, RecommendationEvent
from src.core.advanced_cache import MultiLevelCache, L1MemoryCache
from src.core.enhanced_health import HealthMonitor
from src.core.batch_processing import BatchProcessingEngine
from src.models.ab_testing import MLABTester, ExperimentConfig
from src.models.model_performance import ModelPerformanceMonitor, ModelMetric, MetricType
from src.models.model_optimization import ModelOptimizer, OptimizationStrategy
from src.api.integration import EnhancedFeaturesManager


class TestRealTimeAnalytics:
    """Test real-time analytics functionality."""
    
    @pytest.fixture
    async def analytics_engine(self):
        """Create analytics engine for testing."""
        engine = RealTimeAnalytics(
            redis_url="redis://localhost:6379",
            metrics_retention_hours=1,
            batch_size=10,
            flush_interval=5
        )
        await engine.initialize()
        yield engine
        await engine.cleanup()
    
    @pytest.mark.asyncio
    async def test_user_interaction_tracking(self, analytics_engine):
        """Test user interaction tracking."""
        interaction = UserInteraction(
            user_id="test_user_123",
            event_type="book_view",
            item_id="book_456",
            session_id="session_789"
        )
        
        await analytics_engine.track_user_interaction(interaction)
        
        # Verify interaction was recorded
        metrics = await analytics_engine.get_user_metrics("test_user_123")
        assert metrics is not None
        assert metrics.total_interactions >= 1
    
    @pytest.mark.asyncio
    async def test_recommendation_tracking(self, analytics_engine):
        """Test recommendation event tracking."""
        event = RecommendationEvent(
            user_id="test_user_123",
            session_id="session_789",
            recommendations_shown=5,
            clicks=2,
            response_time_ms=150.0
        )
        
        await analytics_engine.track_recommendation_event(event)
        
        # Verify event was recorded
        metrics = await analytics_engine.get_recommendation_metrics()
        assert metrics.total_recommendations >= 5
        assert metrics.total_clicks >= 2
    
    @pytest.mark.asyncio
    async def test_real_time_metrics(self, analytics_engine):
        """Test real-time metrics aggregation."""
        # Track several interactions
        for i in range(5):
            interaction = UserInteraction(
                user_id=f"user_{i}",
                event_type="book_click",
                item_id=f"book_{i}"
            )
            await analytics_engine.track_user_interaction(interaction)
        
        # Get real-time metrics
        metrics = await analytics_engine.get_real_time_metrics()
        assert metrics.active_users >= 5
        assert metrics.events_per_second >= 0


class TestAdvancedCache:
    """Test advanced caching functionality."""
    
    @pytest.fixture
    async def cache_system(self):
        """Create cache system for testing."""
        l1_cache = L1MemoryCache(max_size=100, ttl_seconds=60)
        cache = MultiLevelCache(
            l1_cache=l1_cache,
            redis_url="redis://localhost:6379",
            default_ttl=300,
            enable_warming=True,
            enable_analytics=True
        )
        await cache.initialize()
        yield cache
        await cache.cleanup()
    
    @pytest.mark.asyncio
    async def test_l1_cache_operations(self, cache_system):
        """Test L1 cache operations."""
        # Set value
        await cache_system.set("test_key", "test_value", ttl=60)
        
        # Get value
        value = await cache_system.get("test_key")
        assert value == "test_value"
        
        # Check L1 cache hit
        value = await cache_system.get("test_key")
        assert value == "test_value"
    
    @pytest.mark.asyncio
    async def test_cache_warming(self, cache_system):
        """Test cache warming functionality."""
        # Define warming function
        async def warm_function(keys):
            return {key: f"warmed_{key}" for key in keys}
        
        # Warm cache
        await cache_system.warm_cache(["key1", "key2"], warm_function)
        
        # Verify warmed values
        value1 = await cache_system.get("key1")
        value2 = await cache_system.get("key2")
        assert value1 == "warmed_key1"
        assert value2 == "warmed_key2"
    
    @pytest.mark.asyncio
    async def test_cache_analytics(self, cache_system):
        """Test cache analytics."""
        # Perform cache operations
        await cache_system.set("analytics_key", "value")
        await cache_system.get("analytics_key")  # Hit
        await cache_system.get("missing_key")    # Miss
        
        # Get analytics
        analytics = await cache_system.get_analytics()
        assert analytics['total_requests'] >= 2
        assert analytics['cache_hits'] >= 1
        assert analytics['cache_misses'] >= 1


class TestEnhancedHealth:
    """Test enhanced health monitoring."""
    
    @pytest.fixture
    async def health_monitor(self):
        """Create health monitor for testing."""
        monitor = HealthMonitor(
            check_interval=5,
            alert_threshold=0.8,
            dependency_timeout=2.0
        )
        yield monitor
        await monitor.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_component_registration(self, health_monitor):
        """Test component registration and health checks."""
        # Register a healthy component
        async def healthy_check():
            return {"status": "healthy", "response_time": 10}
        
        await health_monitor.register_component(
            name="test_service",
            check_func=healthy_check,
            critical=True
        )
        
        # Get health status
        health_report = await health_monitor.get_health_status()
        assert health_report.overall_status == "healthy"
        assert "test_service" in health_report.component_status
    
    @pytest.mark.asyncio
    async def test_unhealthy_component_detection(self, health_monitor):
        """Test detection of unhealthy components."""
        # Register an unhealthy component
        async def unhealthy_check():
            raise Exception("Service unavailable")
        
        await health_monitor.register_component(
            name="failing_service",
            check_func=unhealthy_check,
            critical=True
        )
        
        # Get health status
        health_report = await health_monitor.get_health_status()
        assert health_report.overall_status == "unhealthy"
        assert health_report.component_status["failing_service"]["status"] == "unhealthy"


class TestBatchProcessing:
    """Test batch processing functionality."""
    
    @pytest.fixture
    async def batch_engine(self):
        """Create batch processing engine for testing."""
        engine = BatchProcessingEngine(
            redis_url="redis://localhost:6379",
            max_workers=2,
            queue_maxsize=100,
            result_ttl=3600
        )
        await engine.initialize()
        yield engine
        await engine.cleanup()
    
    @pytest.mark.asyncio
    async def test_job_submission_and_execution(self, batch_engine):
        """Test job submission and execution."""
        # Define a test job
        async def test_job(data):
            await asyncio.sleep(0.1)
            return {"processed": data, "timestamp": datetime.utcnow().isoformat()}
        
        # Submit job
        job_id = await batch_engine.submit_job(
            job_func=test_job,
            job_data={"test": "data"},
            job_type="test_job"
        )
        
        assert job_id is not None
        
        # Wait for completion
        result = await batch_engine.get_job_result(job_id, timeout=5)
        assert result is not None
        assert result["processed"]["test"] == "data"
    
    @pytest.mark.asyncio
    async def test_job_status_tracking(self, batch_engine):
        """Test job status tracking."""
        # Submit a job
        async def slow_job(data):
            await asyncio.sleep(1)
            return {"result": "completed"}
        
        job_id = await batch_engine.submit_job(
            job_func=slow_job,
            job_data={},
            job_type="slow_job"
        )
        
        # Check status
        status = await batch_engine.get_job_status(job_id)
        assert status["status"] in ["pending", "running", "completed"]


class TestMLABTesting:
    """Test ML A/B testing functionality."""
    
    @pytest.fixture
    async def ab_tester(self):
        """Create ML A/B tester for testing."""
        tester = MLABTester(redis_url="redis://localhost:6379")
        await tester.initialize()
        yield tester
        await tester.cleanup()
    
    @pytest.mark.asyncio
    async def test_experiment_creation(self, ab_tester):
        """Test experiment creation."""
        config = ExperimentConfig(
            name="test_experiment",
            description="Test A/B experiment",
            variants=[
                {"name": "control", "model_id": "model_v1"},
                {"name": "treatment", "model_id": "model_v2"}
            ],
            traffic_split={"control": 0.5, "treatment": 0.5},
            minimum_sample_size=100
        )
        
        experiment_id = await ab_tester.create_experiment(config)
        assert experiment_id is not None
    
    @pytest.mark.asyncio
    async def test_variant_assignment(self, ab_tester):
        """Test variant assignment."""
        # Create experiment
        config = ExperimentConfig(
            name="assignment_test",
            variants=[],
            traffic_split={"control": 0.7, "treatment": 0.3}
        )
        experiment_id = await ab_tester.create_experiment(config)
        await ab_tester.start_experiment("assignment_test")
        
        # Test consistent assignment
        user_id = "test_user_123"
        variant1 = await ab_tester.assign_variant(user_id, "assignment_test")
        variant2 = await ab_tester.assign_variant(user_id, "assignment_test")
        
        assert variant1 == variant2  # Should be consistent
        assert variant1 in ["control", "treatment"]


class TestModelPerformanceMonitor:
    """Test model performance monitoring."""
    
    @pytest.fixture
    async def performance_monitor(self):
        """Create performance monitor for testing."""
        monitor = ModelPerformanceMonitor(
            metrics_window_size=100,
            alert_thresholds={'accuracy': 0.8, 'latency_ms': 500}
        )
        await monitor.start_monitoring()
        yield monitor
        await monitor.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_metric_recording(self, performance_monitor):
        """Test metric recording."""
        metric = ModelMetric(
            metric_type=MetricType.ACCURACY,
            value=0.95,
            timestamp=datetime.utcnow(),
            model_id="test_model",
            model_version="v1.0"
        )
        
        await performance_monitor.record_metric(metric)
        
        # Get metrics for the model
        model_metrics = await performance_monitor.get_model_metrics("test_model")
        assert len(model_metrics) >= 1
        assert model_metrics[0]["value"] == 0.95
    
    @pytest.mark.asyncio
    async def test_alert_generation(self, performance_monitor):
        """Test alert generation for threshold breaches."""
        # Record metric that exceeds threshold
        metric = ModelMetric(
            metric_type=MetricType.ACCURACY,
            value=0.7,  # Below threshold of 0.8
            timestamp=datetime.utcnow(),
            model_id="test_model",
            model_version="v1.0"
        )
        
        await performance_monitor.record_metric(metric)
        
        # Check if alert was created
        current_metrics = await performance_monitor.get_current_metrics()
        assert current_metrics["active_alerts_count"] >= 0


class TestModelOptimizer:
    """Test model optimization functionality."""
    
    @pytest.fixture
    async def model_optimizer(self):
        """Create model optimizer for testing."""
        optimizer = ModelOptimizer(
            optimization_strategies=['hyperparameter_tuning'],
            auto_retrain_threshold=0.1
        )
        await optimizer.initialize()
        yield optimizer
        await optimizer.cleanup()
    
    @pytest.mark.asyncio
    async def test_optimization_task_submission(self, model_optimizer):
        """Test optimization task submission."""
        task_id = await model_optimizer.submit_optimization_task(
            strategy=OptimizationStrategy.HYPERPARAMETER_TUNING,
            model_id="test_model",
            parameters={
                'search_space': {
                    'learning_rate': {'type': 'float', 'min': 0.001, 'max': 0.1},
                    'batch_size': {'type': 'int', 'min': 16, 'max': 128}
                },
                'baseline_score': 0.8
            },
            max_trials=5,
            timeout_minutes=1
        )
        
        assert task_id is not None
        
        # Check task status
        status = await model_optimizer.get_task_status(task_id)
        assert status["status"] in ["pending", "running", "completed"]


class TestEnhancedFeaturesIntegration:
    """Test integration of all enhanced features."""
    
    @pytest.fixture
    async def features_manager(self):
        """Create features manager for testing."""
        manager = EnhancedFeaturesManager()
        yield manager
        await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_full_integration_initialization(self, features_manager):
        """Test full integration initialization."""
        # Mock app for testing
        class MockApp:
            def include_router(self, router):
                pass
        
        app = MockApp()
        
        # Initialize all features
        instances = await features_manager.initialize_all(app)
        
        # Verify all instances are created
        assert 'analytics' in instances
        assert 'cache' in instances
        assert 'health' in instances
        assert 'batch' in instances
        assert instances['analytics'] is not None
        assert instances['cache'] is not None


# Utility functions for testing

async def create_test_user_interaction(user_id: str = None) -> UserInteraction:
    """Create a test user interaction."""
    return UserInteraction(
        user_id=user_id or f"user_{uuid.uuid4()}",
        event_type="book_view",
        item_id=f"book_{uuid.uuid4()}",
        session_id=f"session_{uuid.uuid4()}"
    )


async def create_test_recommendation_event(user_id: str = None) -> RecommendationEvent:
    """Create a test recommendation event."""
    return RecommendationEvent(
        user_id=user_id or f"user_{uuid.uuid4()}",
        session_id=f"session_{uuid.uuid4()}",
        recommendations_shown=5,
        clicks=2,
        response_time_ms=120.0
    )


async def create_test_model_metric(model_id: str = "test_model") -> ModelMetric:
    """Create a test model metric."""
    return ModelMetric(
        metric_type=MetricType.ACCURACY,
        value=0.85,
        timestamp=datetime.utcnow(),
        model_id=model_id,
        model_version="v1.0"
    )


# Performance test
@pytest.mark.asyncio
async def test_system_performance_under_load():
    """Test system performance under load."""
    # Create analytics engine
    analytics = RealTimeAnalytics(
        redis_url="redis://localhost:6379",
        batch_size=50,
        flush_interval=1
    )
    await analytics.initialize()
    
    try:
        # Generate load
        tasks = []
        for i in range(100):
            interaction = await create_test_user_interaction(f"load_user_{i}")
            task = analytics.track_user_interaction(interaction)
            tasks.append(task)
        
        # Execute all tasks
        start_time = datetime.utcnow()
        await asyncio.gather(*tasks)
        end_time = datetime.utcnow()
        
        processing_time = (end_time - start_time).total_seconds()
        
        # Verify performance
        assert processing_time < 5.0  # Should process 100 interactions in under 5 seconds
        
        # Get metrics
        metrics = await analytics.get_real_time_metrics()
        assert metrics.total_events >= 100
        
    finally:
        await analytics.cleanup()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
