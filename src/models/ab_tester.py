import numpy as np
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
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
        
    def create_experiment(self, 
                         experiment_id: str,
                         control_model: HybridRecommender,
                         variant_model: HybridRecommender,
                         description: str,
                         metrics: List[str]) -> None:
        """Create a new A/B test experiment."""
        try:
            self.experiments[experiment_id] = {
                'control_model': control_model,
                'variant_model': variant_model,
                'description': description,
                'metrics': metrics,
                'start_date': datetime.now(),
                'status': 'running',
                'sample_size': self._calculate_sample_size(),
                'assignments': {}
            }
            
            logger.info(f"Created experiment {experiment_id}: {description}")
            
        except Exception as e:
            logger.error(f"Error creating experiment: {str(e)}")
            raise
    
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