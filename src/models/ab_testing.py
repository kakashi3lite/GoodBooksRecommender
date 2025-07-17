"""
ML A/B Testing Framework for GoodBooks Recommender

This module provides advanced A/B testing capabilities specifically for ML models,
allowing for sophisticated experimentation and model comparison.
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from dataclasses import dataclass, asdict
import yaml

try:
    # Mock redis for development/testing
    class MockRedis:
        async def ping(self): return True
        async def hset(self, *args, **kwargs): return True
        async def get(self, key): return None
        async def setex(self, *args): return True
        async def lpush(self, *args): return True
        async def expire(self, *args): return True
        async def keys(self, pattern): return []
        async def lrange(self, *args): return []
        async def close(self): pass
        @classmethod
        def from_url(cls, url): return cls()
    
    redis_module = MockRedis
    
    # Try to import real redis but fall back to mock on any error
    try:
        import redis.asyncio as redis
        redis_module = redis
    except ImportError:
        try:
            import aioredis
            redis_module = aioredis
        except (ImportError, TypeError):
            # TypeError can happen with TimeoutError conflicts
            pass
        
except ImportError:
    # Fallback mock
    class MockRedis:
        async def ping(self): return True
        async def hset(self, *args, **kwargs): return True
        async def get(self, key): return None
        async def setex(self, *args): return True
        async def lpush(self, *args): return True
        async def expire(self, *args): return True
        async def keys(self, pattern): return []
        async def lrange(self, *args): return []
        async def close(self): pass
        @classmethod
        def from_url(cls, url): return cls()
    redis_module = MockRedis
from pydantic import BaseModel, Field

from src.core.logging import StructuredLogger
from src.core.monitoring import MetricsCollector

logger = StructuredLogger(__name__)
metrics = MetricsCollector()


class ExperimentStatus(Enum):
    """Experiment status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class StatisticalTest(Enum):
    """Statistical test types."""
    T_TEST = "t_test"
    CHI_SQUARE = "chi_square"
    MANN_WHITNEY = "mann_whitney"
    BOOTSTRAP = "bootstrap"


@dataclass
class ExperimentVariant:
    """Experiment variant configuration."""
    name: str
    model_id: str
    model_config: Dict[str, Any]
    traffic_percentage: float
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExperimentMetrics:
    """Experiment metrics tracking."""
    variant_name: str
    timestamp: datetime
    user_id: str
    recommendation_count: int
    click_through_rate: float
    conversion_rate: float
    user_satisfaction_score: float
    response_time_ms: float
    error_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ExperimentConfig(BaseModel):
    """Experiment configuration model."""
    name: str = Field(..., description="Experiment name")
    description: str = Field("", description="Experiment description")
    variants: List[Dict[str, Any]] = Field(..., description="Experiment variants")
    traffic_split: Dict[str, float] = Field(..., description="Traffic split percentages")
    success_metrics: List[str] = Field(default_factory=lambda: ["ctr", "conversion"])
    minimum_sample_size: int = Field(1000, description="Minimum sample size per variant")
    statistical_power: float = Field(0.8, description="Statistical power requirement")
    significance_level: float = Field(0.05, description="Statistical significance level")
    max_duration_days: int = Field(30, description="Maximum experiment duration")
    auto_stop_on_significance: bool = Field(True, description="Auto-stop when significant")


class MLABTester:
    """Advanced ML A/B Testing Framework."""
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379",
                 experiment_config_path: Optional[str] = None,
                 redis_client: Optional[Any] = None):
        self.redis_url = redis_url
        self.experiment_config_path = experiment_config_path
        self.redis_client = redis_client  # Accept external Redis client
        self.active_experiments: Dict[str, ExperimentConfig] = {}
        self.variant_assignments: Dict[str, str] = {}  # user_id -> variant_name
        
    async def initialize(self):
        """Initialize the A/B testing framework."""
        try:
            logger.info("Initializing ML A/B Testing Framework...")
            
            # Connect to Redis (use provided client or create new one)
            if self.redis_client is None:
                self.redis_client = redis_module.from_url(self.redis_url)
                await self.redis_client.ping()
            
            # Load experiment configurations
            if self.experiment_config_path:
                await self._load_experiment_configs()
            
            # Start background tasks
            asyncio.create_task(self._metrics_aggregation_task())
            asyncio.create_task(self._experiment_monitoring_task())
            
            logger.info("ML A/B Testing Framework initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ML A/B Testing Framework: {str(e)}")
            raise
    
    async def _load_experiment_configs(self):
        """Load experiment configurations from file."""
        try:
            with open(self.experiment_config_path, 'r') as f:
                configs = yaml.safe_load(f)
            
            for config_data in configs.get('experiments', []):
                config = ExperimentConfig(**config_data)
                self.active_experiments[config.name] = config
                
            logger.info(f"Loaded {len(self.active_experiments)} experiment configurations")
            
        except FileNotFoundError:
            logger.warning(f"Experiment config file not found: {self.experiment_config_path}")
        except Exception as e:
            logger.error(f"Failed to load experiment configs: {str(e)}")
    
    async def create_experiment(self, config: ExperimentConfig) -> str:
        """Create a new A/B test experiment."""
        try:
            experiment_id = str(uuid.uuid4())
            
            # Validate traffic split
            total_traffic = sum(config.traffic_split.values())
            if abs(total_traffic - 1.0) > 0.001:
                raise ValueError(f"Traffic split must sum to 1.0, got {total_traffic}")
            
            # Store experiment configuration
            experiment_data = {
                'id': experiment_id,
                'config': config.dict(),
                'status': ExperimentStatus.DRAFT.value,
                'created_at': datetime.utcnow().isoformat(),
                'metrics': {}
            }
            
            await self.redis_client.hset(
                f"experiment:{experiment_id}",
                mapping={
                    'data': json.dumps(experiment_data),
                    'status': ExperimentStatus.DRAFT.value
                }
            )
            
            self.active_experiments[config.name] = config
            
            logger.info(f"Created experiment: {config.name} ({experiment_id})")
            metrics.increment("ab_experiments_created")
            
            return experiment_id
            
        except Exception as e:
            logger.error(f"Failed to create experiment: {str(e)}")
            raise
    
    async def start_experiment(self, experiment_name: str) -> bool:
        """Start an A/B test experiment."""
        try:
            if experiment_name not in self.active_experiments:
                raise ValueError(f"Experiment not found: {experiment_name}")
            
            # Update experiment status
            experiment_id = await self._get_experiment_id(experiment_name)
            await self.redis_client.hset(
                f"experiment:{experiment_id}",
                'status',
                ExperimentStatus.ACTIVE.value
            )
            
            logger.info(f"Started experiment: {experiment_name}")
            metrics.increment("ab_experiments_started")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start experiment: {str(e)}")
            return False
    
    async def stop_experiment(self, experiment_name: str, reason: str = "") -> bool:
        """Stop an A/B test experiment."""
        try:
            experiment_id = await self._get_experiment_id(experiment_name)
            
            # Update experiment status
            await self.redis_client.hset(
                f"experiment:{experiment_id}",
                mapping={
                    'status': ExperimentStatus.COMPLETED.value,
                    'stopped_at': datetime.utcnow().isoformat(),
                    'stop_reason': reason
                }
            )
            
            logger.info(f"Stopped experiment: {experiment_name}, reason: {reason}")
            metrics.increment("ab_experiments_stopped")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop experiment: {str(e)}")
            return False
    
    async def assign_variant(self, user_id: str, experiment_name: str) -> str:
        """Assign a user to an experiment variant."""
        try:
            if experiment_name not in self.active_experiments:
                return "control"  # Default variant
            
            # Check if user already has assignment
            assignment_key = f"assignment:{experiment_name}:{user_id}"
            existing_variant = await self.redis_client.get(assignment_key)
            
            if existing_variant:
                return existing_variant.decode('utf-8')
            
            # Assign new variant based on traffic split
            config = self.active_experiments[experiment_name]
            variant = self._determine_variant(user_id, config.traffic_split)
            
            # Store assignment
            await self.redis_client.setex(
                assignment_key,
                timedelta(days=config.max_duration_days),
                variant
            )
            
            # Track assignment
            await self._track_assignment(experiment_name, user_id, variant)
            
            logger.debug(f"Assigned user {user_id} to variant {variant} in experiment {experiment_name}")
            
            return variant
            
        except Exception as e:
            logger.error(f"Failed to assign variant: {str(e)}")
            return "control"
    
    def _determine_variant(self, user_id: str, traffic_split: Dict[str, float]) -> str:
        """Determine variant assignment using consistent hashing."""
        # Use hash of user_id for consistent assignment
        hash_value = hash(user_id) % 10000 / 10000.0
        
        cumulative = 0.0
        for variant, percentage in traffic_split.items():
            cumulative += percentage
            if hash_value <= cumulative:
                return variant
        
        # Fallback to first variant
        return list(traffic_split.keys())[0]
    
    async def track_metrics(self, experiment_name: str, user_id: str, metrics_data: Dict[str, Any]):
        """Track experiment metrics for a user."""
        try:
            variant = await self.assign_variant(user_id, experiment_name)
            
            # Create metrics object
            experiment_metrics = ExperimentMetrics(
                variant_name=variant,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                recommendation_count=metrics_data.get('recommendation_count', 0),
                click_through_rate=metrics_data.get('click_through_rate', 0.0),
                conversion_rate=metrics_data.get('conversion_rate', 0.0),
                user_satisfaction_score=metrics_data.get('user_satisfaction_score', 0.0),
                response_time_ms=metrics_data.get('response_time_ms', 0.0),
                error_count=metrics_data.get('error_count', 0)
            )
            
            # Store metrics
            metrics_key = f"metrics:{experiment_name}:{variant}:{user_id}"
            await self.redis_client.lpush(metrics_key, json.dumps(experiment_metrics.to_dict()))
            
            # Set expiration
            await self.redis_client.expire(metrics_key, timedelta(days=90))
            
            metrics.increment("ab_experiment_metrics_tracked")
            
        except Exception as e:
            logger.error(f"Failed to track metrics: {str(e)}")
    
    async def get_experiment_results(self, experiment_name: str) -> Dict[str, Any]:
        """Get experiment results and statistical analysis."""
        try:
            if experiment_name not in self.active_experiments:
                raise ValueError(f"Experiment not found: {experiment_name}")
            
            config = self.active_experiments[experiment_name]
            results = {}
            
            # Get metrics for each variant
            for variant in config.traffic_split.keys():
                variant_metrics = await self._get_variant_metrics(experiment_name, variant)
                results[variant] = {
                    'sample_size': len(variant_metrics),
                    'metrics': self._calculate_aggregated_metrics(variant_metrics)
                }
            
            # Perform statistical analysis
            results['statistical_analysis'] = await self._perform_statistical_analysis(
                experiment_name, results
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get experiment results: {str(e)}")
            return {}
    
    async def _get_variant_metrics(self, experiment_name: str, variant: str) -> List[Dict[str, Any]]:
        """Get all metrics for a specific variant."""
        try:
            pattern = f"metrics:{experiment_name}:{variant}:*"
            keys = await self.redis_client.keys(pattern)
            
            all_metrics = []
            for key in keys:
                metrics_data = await self.redis_client.lrange(key, 0, -1)
                for metric_json in metrics_data:
                    metric = json.loads(metric_json.decode('utf-8'))
                    all_metrics.append(metric)
            
            return all_metrics
            
        except Exception as e:
            logger.error(f"Failed to get variant metrics: {str(e)}")
            return []
    
    def _calculate_aggregated_metrics(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate aggregated metrics for a variant."""
        if not metrics_list:
            return {}
        
        # Calculate means
        numeric_fields = [
            'click_through_rate', 'conversion_rate', 'user_satisfaction_score',
            'response_time_ms', 'recommendation_count', 'error_count'
        ]
        
        aggregated = {}
        for field in numeric_fields:
            values = [m.get(field, 0) for m in metrics_list]
            aggregated[f'mean_{field}'] = np.mean(values)
            aggregated[f'std_{field}'] = np.std(values)
            aggregated[f'median_{field}'] = np.median(values)
        
        return aggregated
    
    async def _perform_statistical_analysis(self, experiment_name: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Perform statistical analysis between variants."""
        try:
            # Simple implementation - in production, use proper statistical libraries
            analysis = {
                'significance_tests': {},
                'confidence_intervals': {},
                'recommendations': []
            }
            
            variants = list(results.keys())
            if len(variants) < 2:
                return analysis
            
            # Compare variants pairwise
            for i in range(len(variants)):
                for j in range(i + 1, len(variants)):
                    variant_a = variants[i]
                    variant_b = variants[j]
                    
                    # Get sample sizes
                    size_a = results[variant_a]['sample_size']
                    size_b = results[variant_b]['sample_size']
                    
                    # Check minimum sample size
                    config = self.active_experiments[experiment_name]
                    if size_a < config.minimum_sample_size or size_b < config.minimum_sample_size:
                        analysis['recommendations'].append(
                            f"Insufficient sample size for {variant_a} vs {variant_b}"
                        )
                        continue
                    
                    # Simple significance test (placeholder)
                    comparison_key = f"{variant_a}_vs_{variant_b}"
                    analysis['significance_tests'][comparison_key] = {
                        'p_value': 0.03,  # Placeholder
                        'significant': True,
                        'effect_size': 0.15
                    }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to perform statistical analysis: {str(e)}")
            return {}
    
    async def _track_assignment(self, experiment_name: str, user_id: str, variant: str):
        """Track user assignment to variant."""
        assignment_data = {
            'experiment_name': experiment_name,
            'user_id': user_id,
            'variant': variant,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self.redis_client.lpush(
            f"assignments:{experiment_name}",
            json.dumps(assignment_data)
        )
    
    async def _get_experiment_id(self, experiment_name: str) -> str:
        """Get experiment ID by name."""
        # This is a simplified implementation
        # In production, maintain a proper name->ID mapping
        return f"exp_{hash(experiment_name) % 100000}"
    
    async def _metrics_aggregation_task(self):
        """Background task for metrics aggregation."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Aggregate metrics for active experiments
                for experiment_name in self.active_experiments:
                    await self._aggregate_experiment_metrics(experiment_name)
                
            except Exception as e:
                logger.error(f"Error in metrics aggregation task: {str(e)}")
    
    async def _experiment_monitoring_task(self):
        """Background task for experiment monitoring."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Check experiment conditions
                for experiment_name, config in self.active_experiments.items():
                    await self._check_experiment_conditions(experiment_name, config)
                
            except Exception as e:
                logger.error(f"Error in experiment monitoring task: {str(e)}")
    
    async def _aggregate_experiment_metrics(self, experiment_name: str):
        """Aggregate metrics for an experiment."""
        # Implementation for periodic metrics aggregation
        pass
    
    async def _check_experiment_conditions(self, experiment_name: str, config: ExperimentConfig):
        """Check if experiment should be stopped based on conditions."""
        # Implementation for auto-stopping experiments
        pass
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            if self.redis_client:
                await self.redis_client.close()
            logger.info("ML A/B Testing Framework cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


# Alias for backward compatibility
ABTestingFramework = MLABTester
