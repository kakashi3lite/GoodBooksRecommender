"""
Model Optimization System for GoodBooks Recommender

This module provides automated model optimization including:
- Hyperparameter tuning
- Feature selection
- Model architecture optimization
- Performance optimization
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from abc import ABC, abstractmethod

from src.core.logging import StructuredLogger
from src.core.monitoring import MetricsCollector

logger = StructuredLogger(__name__)
metrics = MetricsCollector()


class OptimizationStrategy(Enum):
    """Optimization strategy types."""
    HYPERPARAMETER_TUNING = "hyperparameter_tuning"
    FEATURE_SELECTION = "feature_selection"
    ARCHITECTURE_SEARCH = "architecture_search"
    ENSEMBLE_OPTIMIZATION = "ensemble_optimization"
    QUANTIZATION = "quantization"
    PRUNING = "pruning"


class OptimizationStatus(Enum):
    """Optimization task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OptimizationTask:
    """Optimization task configuration."""
    task_id: str
    strategy: OptimizationStrategy
    model_id: str
    parameters: Dict[str, Any]
    target_metric: str
    max_trials: int
    timeout_minutes: int
    status: OptimizationStatus = OptimizationStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    best_score: Optional[float] = None
    best_parameters: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['strategy'] = self.strategy.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data


@dataclass
class OptimizationResult:
    """Result of an optimization run."""
    task_id: str
    improved: bool
    improvement_percentage: float
    old_score: float
    new_score: float
    optimized_parameters: Dict[str, Any]
    optimization_time_seconds: float
    trials_completed: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseOptimizer(ABC):
    """Base class for optimization strategies."""
    
    @abstractmethod
    async def optimize(self, 
                      model_id: str, 
                      parameters: Dict[str, Any], 
                      target_metric: str,
                      max_trials: int) -> OptimizationResult:
        """Execute optimization strategy."""
        pass


class HyperparameterOptimizer(BaseOptimizer):
    """Hyperparameter optimization using grid search and random search."""
    
    async def optimize(self, 
                      model_id: str, 
                      parameters: Dict[str, Any], 
                      target_metric: str,
                      max_trials: int) -> OptimizationResult:
        """Optimize hyperparameters."""
        logger.info(f"Starting hyperparameter optimization for model {model_id}")
        
        start_time = time.time()
        best_score = float('-inf')
        best_params = {}
        trials_completed = 0
        
        # Mock optimization (in production, use proper optimization libraries)
        search_space = parameters.get('search_space', {})
        optimization_method = parameters.get('method', 'random')
        
        for trial in range(max_trials):
            # Generate candidate parameters
            candidate_params = self._generate_candidate_parameters(search_space, optimization_method)
            
            # Evaluate model with candidate parameters
            score = await self._evaluate_model(model_id, candidate_params, target_metric)
            
            if score > best_score:
                best_score = score
                best_params = candidate_params.copy()
            
            trials_completed += 1
            
            # Early stopping if we're not improving
            if trial > 10 and best_score == float('-inf'):
                break
        
        optimization_time = time.time() - start_time
        
        # Calculate improvement (using mock baseline)
        baseline_score = parameters.get('baseline_score', best_score * 0.9)
        improvement = ((best_score - baseline_score) / baseline_score) * 100 if baseline_score > 0 else 0
        
        result = OptimizationResult(
            task_id=f"hp_{model_id}_{int(time.time())}",
            improved=best_score > baseline_score,
            improvement_percentage=improvement,
            old_score=baseline_score,
            new_score=best_score,
            optimized_parameters=best_params,
            optimization_time_seconds=optimization_time,
            trials_completed=trials_completed
        )
        
        logger.info(f"Hyperparameter optimization completed: {improvement:.2f}% improvement")
        return result
    
    def _generate_candidate_parameters(self, search_space: Dict[str, Any], method: str) -> Dict[str, Any]:
        """Generate candidate parameters for evaluation."""
        candidate = {}
        
        for param_name, param_config in search_space.items():
            param_type = param_config.get('type', 'float')
            
            if param_type == 'float':
                min_val = param_config.get('min', 0.0)
                max_val = param_config.get('max', 1.0)
                candidate[param_name] = np.random.uniform(min_val, max_val)
            elif param_type == 'int':
                min_val = param_config.get('min', 1)
                max_val = param_config.get('max', 100)
                candidate[param_name] = np.random.randint(min_val, max_val + 1)
            elif param_type == 'choice':
                choices = param_config.get('choices', [])
                if choices:
                    candidate[param_name] = np.random.choice(choices)
        
        return candidate
    
    async def _evaluate_model(self, model_id: str, parameters: Dict[str, Any], target_metric: str) -> float:
        """Evaluate model with given parameters."""
        # Mock evaluation (in production, train and evaluate actual model)
        await asyncio.sleep(0.1)  # Simulate training time
        
        # Return a score based on parameters (mock function)
        base_score = 0.75
        param_bonus = sum(v for v in parameters.values() if isinstance(v, (int, float))) * 0.001
        noise = np.random.normal(0, 0.05)
        
        return min(1.0, max(0.0, base_score + param_bonus + noise))


class FeatureSelectionOptimizer(BaseOptimizer):
    """Feature selection optimization."""
    
    async def optimize(self, 
                      model_id: str, 
                      parameters: Dict[str, Any], 
                      target_metric: str,
                      max_trials: int) -> OptimizationResult:
        """Optimize feature selection."""
        logger.info(f"Starting feature selection optimization for model {model_id}")
        
        start_time = time.time()
        available_features = parameters.get('features', [])
        selection_method = parameters.get('method', 'forward_selection')
        
        best_features = []
        best_score = float('-inf')
        
        if selection_method == 'forward_selection':
            best_features, best_score = await self._forward_selection(
                model_id, available_features, target_metric, max_trials
            )
        elif selection_method == 'backward_elimination':
            best_features, best_score = await self._backward_elimination(
                model_id, available_features, target_metric, max_trials
            )
        
        optimization_time = time.time() - start_time
        
        # Calculate improvement
        baseline_score = parameters.get('baseline_score', best_score * 0.95)
        improvement = ((best_score - baseline_score) / baseline_score) * 100 if baseline_score > 0 else 0
        
        result = OptimizationResult(
            task_id=f"fs_{model_id}_{int(time.time())}",
            improved=best_score > baseline_score,
            improvement_percentage=improvement,
            old_score=baseline_score,
            new_score=best_score,
            optimized_parameters={'selected_features': best_features},
            optimization_time_seconds=optimization_time,
            trials_completed=len(available_features)
        )
        
        logger.info(f"Feature selection optimization completed: {len(best_features)} features selected")
        return result
    
    async def _forward_selection(self, 
                               model_id: str, 
                               features: List[str], 
                               target_metric: str,
                               max_trials: int) -> Tuple[List[str], float]:
        """Forward feature selection."""
        selected_features = []
        remaining_features = features.copy()
        best_score = 0.0
        
        while remaining_features and len(selected_features) < max_trials:
            best_feature = None
            best_trial_score = best_score
            
            for feature in remaining_features:
                trial_features = selected_features + [feature]
                score = await self._evaluate_feature_set(model_id, trial_features, target_metric)
                
                if score > best_trial_score:
                    best_trial_score = score
                    best_feature = feature
            
            if best_feature:
                selected_features.append(best_feature)
                remaining_features.remove(best_feature)
                best_score = best_trial_score
            else:
                break
        
        return selected_features, best_score
    
    async def _backward_elimination(self, 
                                  model_id: str, 
                                  features: List[str], 
                                  target_metric: str,
                                  max_trials: int) -> Tuple[List[str], float]:
        """Backward feature elimination."""
        current_features = features.copy()
        best_score = await self._evaluate_feature_set(model_id, current_features, target_metric)
        
        trials = 0
        while len(current_features) > 1 and trials < max_trials:
            worst_feature = None
            best_trial_score = best_score
            
            for feature in current_features:
                trial_features = [f for f in current_features if f != feature]
                score = await self._evaluate_feature_set(model_id, trial_features, target_metric)
                
                if score >= best_trial_score:
                    best_trial_score = score
                    worst_feature = feature
            
            if worst_feature:
                current_features.remove(worst_feature)
                best_score = best_trial_score
            else:
                break
            
            trials += 1
        
        return current_features, best_score
    
    async def _evaluate_feature_set(self, model_id: str, features: List[str], target_metric: str) -> float:
        """Evaluate model performance with given feature set."""
        # Mock evaluation
        await asyncio.sleep(0.05)
        
        # More features generally better, but with diminishing returns
        base_score = 0.7
        feature_bonus = min(0.25, len(features) * 0.02)
        noise = np.random.normal(0, 0.03)
        
        return min(1.0, max(0.0, base_score + feature_bonus + noise))


class ModelOptimizer:
    """Main model optimization system."""
    
    def __init__(self, 
                 optimization_strategies: List[str] = None,
                 auto_retrain_threshold: float = 0.1,
                 optimization_interval_hours: int = 24):
        self.optimization_strategies = optimization_strategies or ['hyperparameter_tuning']
        self.auto_retrain_threshold = auto_retrain_threshold
        self.optimization_interval_hours = optimization_interval_hours
        
        # Initialize optimizers
        self.optimizers = {
            OptimizationStrategy.HYPERPARAMETER_TUNING: HyperparameterOptimizer(),
            OptimizationStrategy.FEATURE_SELECTION: FeatureSelectionOptimizer()
        }
        
        # Task management
        self.optimization_tasks: Dict[str, OptimizationTask] = {}
        self.optimization_results: Dict[str, OptimizationResult] = {}
        self.task_queue = asyncio.Queue()
        
        # Background processing
        self.processing_active = False
        self.processing_task = None
        
    async def initialize(self):
        """Initialize the optimization system."""
        logger.info("Initializing model optimization system...")
        
        self.processing_active = True
        self.processing_task = asyncio.create_task(self._process_optimization_tasks())
        
        # Start periodic optimization
        asyncio.create_task(self._periodic_optimization())
        
        logger.info("Model optimization system initialized")
    
    async def submit_optimization_task(self, 
                                     strategy: OptimizationStrategy,
                                     model_id: str,
                                     parameters: Dict[str, Any],
                                     target_metric: str = 'accuracy',
                                     max_trials: int = 50,
                                     timeout_minutes: int = 60) -> str:
        """Submit an optimization task."""
        task_id = f"{strategy.value}_{model_id}_{int(time.time())}"
        
        task = OptimizationTask(
            task_id=task_id,
            strategy=strategy,
            model_id=model_id,
            parameters=parameters,
            target_metric=target_metric,
            max_trials=max_trials,
            timeout_minutes=timeout_minutes
        )
        
        self.optimization_tasks[task_id] = task
        await self.task_queue.put(task)
        
        logger.info(f"Optimization task submitted: {task_id}")
        metrics.increment("optimization_tasks_submitted", {"strategy": strategy.value})
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of an optimization task."""
        if task_id not in self.optimization_tasks:
            return {"error": "Task not found"}
        
        task = self.optimization_tasks[task_id]
        status = task.to_dict()
        
        # Add result if available
        if task_id in self.optimization_results:
            status['result'] = self.optimization_results[task_id].to_dict()
        
        return status
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel an optimization task."""
        if task_id not in self.optimization_tasks:
            return False
        
        task = self.optimization_tasks[task_id]
        if task.status in [OptimizationStatus.PENDING, OptimizationStatus.RUNNING]:
            task.status = OptimizationStatus.CANCELLED
            logger.info(f"Optimization task cancelled: {task_id}")
            return True
        
        return False
    
    async def get_optimization_history(self, model_id: str) -> List[Dict[str, Any]]:
        """Get optimization history for a model."""
        history = []
        
        for task in self.optimization_tasks.values():
            if task.model_id == model_id:
                task_data = task.to_dict()
                if task.task_id in self.optimization_results:
                    task_data['result'] = self.optimization_results[task.task_id].to_dict()
                history.append(task_data)
        
        # Sort by creation time
        history.sort(key=lambda x: x['created_at'], reverse=True)
        return history
    
    async def _process_optimization_tasks(self):
        """Process optimization tasks from the queue."""
        while self.processing_active:
            try:
                # Get task from queue
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                if task.status == OptimizationStatus.CANCELLED:
                    continue
                
                # Execute optimization
                await self._execute_optimization_task(task)
                
            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error processing optimization task: {str(e)}")
    
    async def _execute_optimization_task(self, task: OptimizationTask):
        """Execute an optimization task."""
        try:
            task.status = OptimizationStatus.RUNNING
            task.started_at = datetime.utcnow()
            
            logger.info(f"Executing optimization task: {task.task_id}")
            
            # Get appropriate optimizer
            optimizer = self.optimizers.get(task.strategy)
            if not optimizer:
                raise ValueError(f"No optimizer available for strategy: {task.strategy}")
            
            # Execute optimization with timeout
            result = await asyncio.wait_for(
                optimizer.optimize(
                    task.model_id,
                    task.parameters,
                    task.target_metric,
                    task.max_trials
                ),
                timeout=task.timeout_minutes * 60
            )
            
            # Store result
            self.optimization_results[task.task_id] = result
            task.status = OptimizationStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.best_score = result.new_score
            task.best_parameters = result.optimized_parameters
            
            logger.info(f"Optimization task completed: {task.task_id}")
            metrics.increment("optimization_tasks_completed", {"strategy": task.strategy.value})
            
            # Check if model should be retrained
            if result.improved and result.improvement_percentage >= (self.auto_retrain_threshold * 100):
                await self._trigger_model_retrain(task.model_id, result.optimized_parameters)
            
        except asyncio.TimeoutError:
            task.status = OptimizationStatus.FAILED
            task.error_message = "Optimization timed out"
            logger.error(f"Optimization task timed out: {task.task_id}")
            
        except Exception as e:
            task.status = OptimizationStatus.FAILED
            task.error_message = str(e)
            logger.error(f"Optimization task failed: {task.task_id}, error: {str(e)}")
            
        finally:
            if task.completed_at is None:
                task.completed_at = datetime.utcnow()
    
    async def _trigger_model_retrain(self, model_id: str, optimized_parameters: Dict[str, Any]):
        """Trigger model retraining with optimized parameters."""
        logger.info(f"Triggering model retrain for {model_id} with optimized parameters")
        
        # In production, this would trigger actual model retraining
        # For now, just log the event
        metrics.increment("model_retrains_triggered", {"model_id": model_id})
    
    async def _periodic_optimization(self):
        """Periodic automatic optimization."""
        while self.processing_active:
            try:
                await asyncio.sleep(self.optimization_interval_hours * 3600)
                
                # Trigger optimization for models that need it
                await self._auto_optimize_models()
                
            except Exception as e:
                logger.error(f"Error in periodic optimization: {str(e)}")
    
    async def _auto_optimize_models(self):
        """Automatically optimize models that need optimization."""
        # In production, this would analyze model performance and
        # trigger optimization for underperforming models
        logger.info("Checking models for automatic optimization...")
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up model optimization system...")
        
        self.processing_active = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Model optimization system cleanup completed")
