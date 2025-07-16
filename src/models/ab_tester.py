import numpy as np
import pandas as pd
import logging
import redis
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from scipy import stats
from src.models.hybrid_recommender import HybridRecommender
from src.data.data_loader import DataLoader
from src.config import Config

logger = logging.getLogger(__name__)

class ABTester:
    def __init__(self, config: Config):
        self.config = config
        self.data_loader = DataLoader(config)
        self.experiments: Dict[str, Dict[str, Any]] = {}
        self.results: Dict[str, Dict[str, Any]] = {}
        
        # Redis for persistent storage and real-time metrics
        self.redis_client = self._init_redis()
        
        # Request routing support
        self._routing_strategies = {
            'random': self._random_routing,
            'weighted': self._weighted_routing,
            'staged': self._staged_routing
        }
        
    def _init_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis connection for experiment data persistence."""
        try:
            redis_client = redis.Redis(
                host=getattr(self.config, 'REDIS_HOST', 'localhost'),
                port=getattr(self.config, 'REDIS_PORT', 6379),
                db=getattr(self.config, 'REDIS_AB_DB', 2),
                decode_responses=True
            )
            redis_client.ping()
            logger.info("Redis connection established for A/B testing")
            return redis_client
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory storage: {str(e)}")
            return None

    def create_experiment(self, 
                         experiment_id: str,
                         control_model: HybridRecommender,
                         variant_model: HybridRecommender,
                         description: str,
                         metrics: List[str],
                         traffic_split: float = 0.5,
                         routing_strategy: str = 'random') -> None:
        """
        Create a new A/B test experiment with request routing support.
        
        Args:
            experiment_id: Unique identifier for the experiment
            control_model: Control (current) model
            variant_model: Variant (new) model to test
            description: Description of the experiment
            metrics: List of metrics to track
            traffic_split: Percentage of traffic to send to variant (0.0-1.0)
            routing_strategy: Strategy for routing requests ('random', 'weighted', 'staged')
        """
        try:
            experiment_config = {
                'control_model': control_model,
                'variant_model': variant_model,
                'description': description,
                'metrics': metrics,
                'start_date': datetime.now(),
                'status': 'running',
                'sample_size': self._calculate_sample_size(),
                'assignments': {},
                'traffic_split': traffic_split,
                'routing_strategy': routing_strategy,
                'total_requests': 0,
                'control_requests': 0,
                'variant_requests': 0,
                'real_time_metrics': {metric: {'control': [], 'variant': []} for metric in metrics}
            }
            
            self.experiments[experiment_id] = experiment_config
            
            # Persist to Redis if available
            if self.redis_client:
                self._save_experiment_to_redis(experiment_id, experiment_config)
            
            logger.info(f"Created experiment {experiment_id} with {traffic_split*100}% traffic split")
            
        except Exception as e:
            logger.error(f"Error creating experiment: {str(e)}")
            raise

    def route_request(self, experiment_id: str, user_id: int, request_context: Dict[str, Any] = None) -> str:
        """
        Route a request to control or variant model based on experiment configuration.
        
        Args:
            experiment_id: ID of the experiment
            user_id: User making the request
            request_context: Additional context for routing decisions
            
        Returns:
            'control' or 'variant' indicating which model to use
        """
        try:
            if experiment_id not in self.experiments:
                return 'control'  # Default to control if experiment not found
            
            experiment = self.experiments[experiment_id]
            
            if experiment['status'] != 'running':
                return 'control'
            
            # Use routing strategy
            strategy = experiment['routing_strategy']
            routing_func = self._routing_strategies.get(strategy, self._random_routing)
            
            assignment = routing_func(experiment, user_id, request_context)
            
            # Update request counts
            experiment['total_requests'] += 1
            if assignment == 'control':
                experiment['control_requests'] += 1
            else:
                experiment['variant_requests'] += 1
            
            # Store user assignment
            experiment['assignments'][user_id] = assignment
            
            # Update Redis
            if self.redis_client:
                self._update_experiment_in_redis(experiment_id, experiment)
            
            return assignment
            
        except Exception as e:
            logger.error(f"Error routing request: {str(e)}")
            return 'control'  # Fail safe to control

    def _random_routing(self, experiment: Dict[str, Any], user_id: int, context: Dict[str, Any]) -> str:
        """Random assignment based on traffic split."""
        traffic_split = experiment['traffic_split']
        
        # Use deterministic hash for consistent assignment
        hash_value = hash(f"{user_id}_{experiment['start_date']}")
        normalized_hash = (hash_value % 10000) / 10000.0
        
        return 'variant' if normalized_hash < traffic_split else 'control'

    def _weighted_routing(self, experiment: Dict[str, Any], user_id: int, context: Dict[str, Any]) -> str:
        """Weighted assignment considering user characteristics."""
        base_split = experiment['traffic_split']
        
        # Adjust split based on user characteristics (if available in context)
        adjusted_split = base_split
        
        if context:
            # Example: increase variant exposure for power users
            if context.get('user_activity_level') == 'high':
                adjusted_split = min(base_split * 1.2, 1.0)
            elif context.get('user_activity_level') == 'low':
                adjusted_split = base_split * 0.8
        
        hash_value = hash(f"{user_id}_{experiment['start_date']}")
        normalized_hash = (hash_value % 10000) / 10000.0
        
        return 'variant' if normalized_hash < adjusted_split else 'control'

    def _staged_routing(self, experiment: Dict[str, Any], user_id: int, context: Dict[str, Any]) -> str:
        """Staged rollout - gradually increase traffic to variant."""
        base_split = experiment['traffic_split']
        days_running = (datetime.now() - experiment['start_date']).days
        
        # Gradually ramp up over 7 days
        ramp_factor = min(days_running / 7.0, 1.0)
        effective_split = base_split * ramp_factor
        
        hash_value = hash(f"{user_id}_{experiment['start_date']}")
        normalized_hash = (hash_value % 10000) / 10000.0
        
        return 'variant' if normalized_hash < effective_split else 'control'

    def record_real_time_metric(self, 
                               experiment_id: str,
                               user_id: int,
                               metric_name: str,
                               value: float,
                               timestamp: Optional[datetime] = None) -> None:
        """
        Record real-time metrics during the experiment.
        
        Args:
            experiment_id: ID of the experiment
            user_id: User ID associated with the metric
            metric_name: Name of the metric
            value: Metric value
            timestamp: When the metric was recorded
        """
        try:
            if experiment_id not in self.experiments:
                return
            
            experiment = self.experiments[experiment_id]
            assignment = experiment['assignments'].get(user_id, 'control')
            
            metric_data = {
                'user_id': user_id,
                'value': value,
                'timestamp': (timestamp or datetime.now()).isoformat(),
                'assignment': assignment
            }
            
            # Store in experiment
            if metric_name in experiment['real_time_metrics']:
                experiment['real_time_metrics'][metric_name][assignment].append(metric_data)
            
            # Store in Redis for real-time analysis
            if self.redis_client:
                redis_key = f"ab_metric:{experiment_id}:{metric_name}:{assignment}"
                self.redis_client.lpush(redis_key, json.dumps(metric_data))
                
                # Keep only last 10000 entries per metric
                self.redis_client.ltrim(redis_key, 0, 9999)
            
        except Exception as e:
            logger.error(f"Error recording real-time metric: {str(e)}")

    def get_real_time_results(self, experiment_id: str, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Get real-time experiment results for a specific time window.
        
        Args:
            experiment_id: ID of the experiment
            time_window_hours: Hours of recent data to analyze
            
        Returns:
            Real-time analysis results
        """
        try:
            if experiment_id not in self.experiments:
                return {}
            
            experiment = self.experiments[experiment_id]
            cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
            
            results = {
                'experiment_id': experiment_id,
                'time_window_hours': time_window_hours,
                'traffic_split': {
                    'control': experiment['control_requests'],
                    'variant': experiment['variant_requests'],
                    'total': experiment['total_requests']
                },
                'metrics': {}
            }
            
            for metric_name in experiment['metrics']:
                metric_results = self._analyze_real_time_metric(
                    experiment_id, metric_name, cutoff_time
                )
                results['metrics'][metric_name] = metric_results
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting real-time results: {str(e)}")
            return {}

    def _analyze_real_time_metric(self, 
                                 experiment_id: str, 
                                 metric_name: str, 
                                 cutoff_time: datetime) -> Dict[str, Any]:
        """Analyze a specific metric in real-time."""
        try:
            experiment = self.experiments[experiment_id]
            
            # Get recent data
            control_data = []
            variant_data = []
            
            if self.redis_client:
                # Get from Redis
                control_key = f"ab_metric:{experiment_id}:{metric_name}:control"
                variant_key = f"ab_metric:{experiment_id}:{metric_name}:variant"
                
                control_raw = self.redis_client.lrange(control_key, 0, -1)
                variant_raw = self.redis_client.lrange(variant_key, 0, -1)
                
                for item in control_raw:
                    data = json.loads(item)
                    timestamp = datetime.fromisoformat(data['timestamp'])
                    if timestamp >= cutoff_time:
                        control_data.append(data['value'])
                
                for item in variant_raw:
                    data = json.loads(item)
                    timestamp = datetime.fromisoformat(data['timestamp'])
                    if timestamp >= cutoff_time:
                        variant_data.append(data['value'])
            else:
                # Get from in-memory storage
                for entry in experiment['real_time_metrics'][metric_name]['control']:
                    timestamp = datetime.fromisoformat(entry['timestamp'])
                    if timestamp >= cutoff_time:
                        control_data.append(entry['value'])
                
                for entry in experiment['real_time_metrics'][metric_name]['variant']:
                    timestamp = datetime.fromisoformat(entry['timestamp'])
                    if timestamp >= cutoff_time:
                        variant_data.append(entry['value'])
            
            if not control_data or not variant_data:
                return {'status': 'insufficient_data'}
            
            # Calculate statistics
            control_mean = np.mean(control_data)
            variant_mean = np.mean(variant_data)
            
            # Perform t-test
            statistic, p_value = stats.ttest_ind(variant_data, control_data)
            
            # Calculate effect size (Cohen's d)
            pooled_std = np.sqrt(((len(control_data) - 1) * np.var(control_data, ddof=1) + 
                                (len(variant_data) - 1) * np.var(variant_data, ddof=1)) / 
                               (len(control_data) + len(variant_data) - 2))
            effect_size = (variant_mean - control_mean) / pooled_std if pooled_std > 0 else 0
            
            return {
                'control_mean': control_mean,
                'variant_mean': variant_mean,
                'control_sample_size': len(control_data),
                'variant_sample_size': len(variant_data),
                'relative_improvement': ((variant_mean - control_mean) / control_mean * 100) if control_mean != 0 else 0,
                'p_value': p_value,
                'effect_size': effect_size,
                'significant': p_value < 0.05,
                'confidence_interval': self._calculate_confidence_interval(control_data, variant_data),
                'status': 'ready' if min(len(control_data), len(variant_data)) >= 30 else 'collecting_data'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing real-time metric: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def auto_stop_experiment(self, experiment_id: str, confidence_threshold: float = 0.95) -> bool:
        """
        Automatically stop experiment if results are conclusive.
        
        Args:
            experiment_id: ID of the experiment
            confidence_threshold: Confidence threshold for stopping
            
        Returns:
            True if experiment was stopped
        """
        try:
            results = self.get_real_time_results(experiment_id)
            
            if not results or 'metrics' not in results:
                return False
            
            # Check if we have enough data and significant results
            significant_metrics = 0
            total_metrics = len(results['metrics'])
            
            for metric_name, metric_data in results['metrics'].items():
                if (metric_data.get('status') == 'ready' and 
                    metric_data.get('significant', False) and
                    metric_data.get('p_value', 1.0) < (1 - confidence_threshold)):
                    significant_metrics += 1
            
            # Stop if majority of metrics show significant results
            if significant_metrics >= total_metrics * 0.6:
                self.stop_experiment(experiment_id)
                logger.info(f"Auto-stopped experiment {experiment_id} due to significant results")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in auto-stop check: {str(e)}")
            return False

    def stop_experiment(self, experiment_id: str) -> None:
        """Stop a running experiment."""
        if experiment_id in self.experiments:
            self.experiments[experiment_id]['status'] = 'stopped'
            self.experiments[experiment_id]['end_date'] = datetime.now()
            
            if self.redis_client:
                self._update_experiment_in_redis(experiment_id, self.experiments[experiment_id])
            
            logger.info(f"Stopped experiment {experiment_id}")

    def _save_experiment_to_redis(self, experiment_id: str, experiment: Dict[str, Any]) -> None:
        """Save experiment configuration to Redis."""
        try:
            # Convert non-serializable objects to serializable format
            serializable_experiment = experiment.copy()
            serializable_experiment['control_model'] = 'control_model_ref'
            serializable_experiment['variant_model'] = 'variant_model_ref'
            serializable_experiment['start_date'] = experiment['start_date'].isoformat()
            
            redis_key = f"ab_experiment:{experiment_id}"
            self.redis_client.set(redis_key, json.dumps(serializable_experiment, default=str))
            
        except Exception as e:
            logger.error(f"Error saving experiment to Redis: {str(e)}")

    def _update_experiment_in_redis(self, experiment_id: str, experiment: Dict[str, Any]) -> None:
        """Update experiment statistics in Redis."""
        try:
            redis_key = f"ab_experiment_stats:{experiment_id}"
            stats = {
                'total_requests': experiment['total_requests'],
                'control_requests': experiment['control_requests'],
                'variant_requests': experiment['variant_requests'],
                'status': experiment['status'],
                'last_updated': datetime.now().isoformat()
            }
            self.redis_client.set(redis_key, json.dumps(stats))
            
        except Exception as e:
            logger.error(f"Error updating experiment in Redis: {str(e)}")

    def _calculate_sample_size(self, 
                              effect_size: float = 0.1,
                              alpha: float = 0.05,
                              power: float = 0.8) -> int:
        """Calculate required sample size for the experiment."""
        try:
            # Using two-sided t-test sample size calculation
            sample_size = stats.tt_ind_solve_power(
                effect_size=effect_size,
                alpha=alpha,
                power=power,
                ratio=1.0,
                alternative='two-sided'
            )
            
            return int(np.ceil(sample_size))
            
        except Exception as e:
            logger.error(f"Error calculating sample size: {str(e)}")
            raise
    
    def assign_user(self, user_id: int, experiment_id: str) -> str:
        """Assign a user to either control or variant group."""
        try:
            if experiment_id not in self.experiments:
                raise ValueError(f"Experiment {experiment_id} not found")
                
            if user_id in self.experiments[experiment_id]['assignments']:
                return self.experiments[experiment_id]['assignments'][user_id]
            
            # Deterministic but random-looking assignment using hash
            assignment = 'control' if hash(f"{user_id}{experiment_id}") % 2 == 0 else 'variant'
            self.experiments[experiment_id]['assignments'][user_id] = assignment
            
            return assignment
            
        except Exception as e:
            logger.error(f"Error assigning user: {str(e)}")
            raise
    
    def record_interaction(self,
                          experiment_id: str,
                          user_id: int,
                          book_id: int,
                          metrics: Dict[str, float]) -> None:
        """Record user interaction metrics for the experiment."""
        try:
            if experiment_id not in self.experiments:
                raise ValueError(f"Experiment {experiment_id} not found")
                
            experiment = self.experiments[experiment_id]
            group = self.assign_user(user_id, experiment_id)
            
            # Initialize metrics storage if needed
            if 'metrics_data' not in experiment:
                experiment['metrics_data'] = {'control': {}, 'variant': {}}
            
            # Store metrics
            if user_id not in experiment['metrics_data'][group]:
                experiment['metrics_data'][group][user_id] = []
            
            experiment['metrics_data'][group][user_id].append({
                'timestamp': datetime.now(),
                'book_id': book_id,
                'metrics': metrics
            })
            
        except Exception as e:
            logger.error(f"Error recording interaction: {str(e)}")
            raise
    
    def analyze_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Analyze the results of an experiment."""
        try:
            if experiment_id not in self.experiments:
                raise ValueError(f"Experiment {experiment_id} not found")
                
            experiment = self.experiments[experiment_id]
            
            if 'metrics_data' not in experiment:
                raise ValueError("No data collected for this experiment")
                
            results = {
                'experiment_id': experiment_id,
                'description': experiment['description'],
                'duration': (datetime.now() - experiment['start_date']).days,
                'sample_sizes': {
                    'control': len(experiment['metrics_data']['control']),
                    'variant': len(experiment['metrics_data']['variant'])
                },
                'metrics': {}
            }
            
            # Analyze each metric
            for metric in experiment['metrics']:
                metric_results = self._analyze_metric(
                    experiment['metrics_data']['control'],
                    experiment['metrics_data']['variant'],
                    metric
                )
                results['metrics'][metric] = metric_results
            
            # Calculate overall recommendation
            results['recommendation'] = self._generate_recommendation(results['metrics'])
            
            self.results[experiment_id] = results
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing experiment: {str(e)}")
            raise
    
    def _analyze_metric(self,
                        control_data: Dict[int, List[Dict[str, Any]]],
                        variant_data: Dict[int, List[Dict[str, Any]]],
                        metric: str) -> Dict[str, Any]:
        """Analyze a specific metric from the experiment data."""
        try:
            # Extract metric values
            control_values = []
            variant_values = []
            
            for user_data in control_data.values():
                control_values.extend([d['metrics'][metric] for d in user_data if metric in d['metrics']])
            
            for user_data in variant_data.values():
                variant_values.extend([d['metrics'][metric] for d in user_data if metric in d['metrics']])
            
            # Calculate statistics
            control_mean = np.mean(control_values)
            variant_mean = np.mean(variant_values)
            relative_improvement = (variant_mean - control_mean) / control_mean
            
            # Perform t-test
            t_stat, p_value = stats.ttest_ind(control_values, variant_values)
            
            return {
                'control_mean': float(control_mean),
                'variant_mean': float(variant_mean),
                'relative_improvement': float(relative_improvement),
                'p_value': float(p_value),
                'significant': p_value < 0.05,
                'confidence_interval': self._calculate_confidence_interval(control_values, variant_values)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing metric: {str(e)}")
            raise
    
    def _calculate_confidence_interval(self,
                                      control_values: List[float],
                                      variant_values: List[float],
                                      confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval for the difference between variant and control."""
        try:
            # Calculate mean difference
            mean_diff = np.mean(variant_values) - np.mean(control_values)
            
            # Calculate standard error of the difference
            se = np.sqrt(np.var(control_values)/len(control_values) + 
                        np.var(variant_values)/len(variant_values))
            
            # Calculate confidence interval
            z_score = stats.norm.ppf((1 + confidence) / 2)
            margin = z_score * se
            
            return (float(mean_diff - margin), float(mean_diff + margin))
            
        except Exception as e:
            logger.error(f"Error calculating confidence interval: {str(e)}")
            raise
    
    def _generate_recommendation(self, metrics_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a recommendation based on the experiment results."""
        try:
            significant_improvements = 0
            significant_degradations = 0
            total_metrics = len(metrics_results)
            
            for metric, results in metrics_results.items():
                if results['significant']:
                    if results['relative_improvement'] > 0:
                        significant_improvements += 1
                    else:
                        significant_degradations += 1
            
            # Decision logic
            if significant_degradations > 0:
                decision = 'rollback'
                reason = f"Found {significant_degradations} significant metric degradations"
            elif significant_improvements > total_metrics / 2:
                decision = 'ship'
                reason = f"Found improvements in {significant_improvements} out of {total_metrics} metrics"
            else:
                decision = 'continue'
                reason = "Results inconclusive, need more data"
            
            return {
                'decision': decision,
                'reason': reason,
                'confidence': self._calculate_decision_confidence(metrics_results)
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {str(e)}")
            raise
    
    def _calculate_decision_confidence(self, metrics_results: Dict[str, Dict[str, Any]]) -> float:
        """Calculate confidence in the experiment decision."""
        try:
            # Weight p-values by relative improvement
            weighted_confidence = 0
            total_weight = 0
            
            for results in metrics_results.values():
                weight = abs(results['relative_improvement'])
                confidence = 1 - results['p_value']
                weighted_confidence += weight * confidence
                total_weight += weight
            
            return float(weighted_confidence / total_weight if total_weight > 0 else 0)
            
        except Exception as e:
            logger.error(f"Error calculating decision confidence: {str(e)}")
            raise