import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
import logging
from collections import defaultdict
from sklearn.metrics import ndcg_score
from src.config import Config
from src.user.interaction_tracker import InteractionTracker

logger = logging.getLogger(__name__)

class RecommendationMetrics:
    def __init__(self, config: Config, interaction_tracker: InteractionTracker):
        self.config = config
        self.interaction_tracker = interaction_tracker
        self.metrics_history: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.recommendation_logs: List[Dict[str, Any]] = []
        
    def log_recommendation(self,
                          user_id: int,
                          recommended_items: List[int],
                          scores: List[float],
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log a recommendation event for analysis."""
        try:
            log_entry = {
                'timestamp': datetime.now(),
                'user_id': user_id,
                'items': recommended_items,
                'scores': scores,
                'metadata': metadata or {}
            }
            self.recommendation_logs.append(log_entry)
            
        except Exception as e:
            logger.error(f"Error logging recommendation: {str(e)}")
    
    def calculate_metrics(self,
                         time_window: Optional[timedelta] = None,
                         k_values: Optional[List[int]] = None) -> Dict[str, Any]:
        """Calculate comprehensive recommendation metrics."""
        try:
            # Set default k values if not provided
            k_values = k_values or [5, 10, 20]
            
            # Get relevant recommendations and interactions
            recommendations = self._get_filtered_recommendations(time_window)
            if not recommendations:
                return {}
            
            # Calculate metrics
            metrics = {
                'accuracy': self._calculate_accuracy_metrics(recommendations, k_values),
                'ranking': self._calculate_ranking_metrics(recommendations, k_values),
                'diversity': self._calculate_diversity_metrics(recommendations),
                'coverage': self._calculate_coverage_metrics(recommendations),
                'personalization': self._calculate_personalization_metrics(recommendations),
                'temporal': self._calculate_temporal_metrics(recommendations),
                'business': self._calculate_business_metrics(recommendations)
            }
            
            # Store metrics history
            self._update_metrics_history(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            raise
    
    def _get_filtered_recommendations(self,
                                     time_window: Optional[timedelta]) -> List[Dict[str, Any]]:
        """Get filtered recommendations based on time window."""
        try:
            if not time_window:
                return self.recommendation_logs
            
            cutoff_time = datetime.now() - time_window
            return [
                log for log in self.recommendation_logs
                if log['timestamp'] >= cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"Error filtering recommendations: {str(e)}")
            return []
    
    def _calculate_accuracy_metrics(self,
                                   recommendations: List[Dict[str, Any]],
                                   k_values: List[int]) -> Dict[str, Dict[int, float]]:
        """Calculate accuracy-based metrics."""
        try:
            metrics = {
                'precision': {},
                'recall': {},
                'ndcg': {},
                'map': {}
            }
            
            for k in k_values:
                # Calculate metrics at each k
                precision_k = self._calculate_precision_at_k(recommendations, k)
                recall_k = self._calculate_recall_at_k(recommendations, k)
                ndcg_k = self._calculate_ndcg_at_k(recommendations, k)
                map_k = self._calculate_map_at_k(recommendations, k)
                
                metrics['precision'][k] = precision_k
                metrics['recall'][k] = recall_k
                metrics['ndcg'][k] = ndcg_k
                metrics['map'][k] = map_k
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating accuracy metrics: {str(e)}")
            return {}
    
    def _calculate_precision_at_k(self,
                                 recommendations: List[Dict[str, Any]],
                                 k: int) -> float:
        """Calculate precision@k."""
        try:
            if not recommendations:
                return 0.0
            
            precisions = []
            for rec in recommendations:
                user_id = rec['user_id']
                recommended_items = set(rec['items'][:k])
                
                # Get user interactions after recommendation
                interactions = self._get_user_interactions_after(user_id, rec['timestamp'])
                interacted_items = set(interactions)
                
                # Calculate precision
                if recommended_items:
                    precision = len(recommended_items & interacted_items) / len(recommended_items)
                    precisions.append(precision)
            
            return float(np.mean(precisions)) if precisions else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating precision@{k}: {str(e)}")
            return 0.0
    
    def _calculate_recall_at_k(self,
                               recommendations: List[Dict[str, Any]],
                               k: int) -> float:
        """Calculate recall@k."""
        try:
            if not recommendations:
                return 0.0
            
            recalls = []
            for rec in recommendations:
                user_id = rec['user_id']
                recommended_items = set(rec['items'][:k])
                
                # Get user interactions after recommendation
                interactions = self._get_user_interactions_after(user_id, rec['timestamp'])
                interacted_items = set(interactions)
                
                # Calculate recall
                if interacted_items:
                    recall = len(recommended_items & interacted_items) / len(interacted_items)
                    recalls.append(recall)
            
            return float(np.mean(recalls)) if recalls else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating recall@{k}: {str(e)}")
            return 0.0
    
    def _calculate_ndcg_at_k(self,
                             recommendations: List[Dict[str, Any]],
                             k: int) -> float:
        """Calculate NDCG@k."""
        try:
            if not recommendations:
                return 0.0
            
            ndcg_scores = []
            for rec in recommendations:
                user_id = rec['user_id']
                recommended_items = rec['items'][:k]
                scores = rec['scores'][:k]
                
                # Get user interactions after recommendation
                interactions = self._get_user_interactions_after(user_id, rec['timestamp'])
                
                # Create relevance vector
                relevance = [1 if item in interactions else 0 for item in recommended_items]
                
                if any(relevance):
                    # Calculate NDCG using sklearn
                    ndcg = ndcg_score([relevance], [scores])
                    ndcg_scores.append(ndcg)
            
            return float(np.mean(ndcg_scores)) if ndcg_scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating NDCG@{k}: {str(e)}")
            return 0.0
    
    def _calculate_map_at_k(self,
                            recommendations: List[Dict[str, Any]],
                            k: int) -> float:
        """Calculate MAP@k."""
        try:
            if not recommendations:
                return 0.0
            
            ap_scores = []
            for rec in recommendations:
                user_id = rec['user_id']
                recommended_items = rec['items'][:k]
                
                # Get user interactions after recommendation
                interactions = self._get_user_interactions_after(user_id, rec['timestamp'])
                interacted_items = set(interactions)
                
                # Calculate average precision
                if interacted_items:
                    relevant_count = 0
                    precision_sum = 0
                    
                    for i, item in enumerate(recommended_items, 1):
                        if item in interacted_items:
                            relevant_count += 1
                            precision_sum += relevant_count / i
                    
                    ap = precision_sum / len(interacted_items) if interacted_items else 0
                    ap_scores.append(ap)
            
            return float(np.mean(ap_scores)) if ap_scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating MAP@{k}: {str(e)}")
            return 0.0
    
    def _calculate_ranking_metrics(self,
                                  recommendations: List[Dict[str, Any]],
                                  k_values: List[int]) -> Dict[str, Any]:
        """Calculate ranking-based metrics."""
        try:
            metrics = {
                'mrr': self._calculate_mrr(recommendations),
                'arhr': {k: self._calculate_arhr_at_k(recommendations, k) for k in k_values},
                'rank_correlation': self._calculate_rank_correlation(recommendations)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating ranking metrics: {str(e)}")
            return {}
    
    def _calculate_mrr(self, recommendations: List[Dict[str, Any]]) -> float:
        """Calculate Mean Reciprocal Rank."""
        try:
            if not recommendations:
                return 0.0
            
            reciprocal_ranks = []
            for rec in recommendations:
                user_id = rec['user_id']
                recommended_items = rec['items']
                
                # Get user interactions after recommendation
                interactions = self._get_user_interactions_after(user_id, rec['timestamp'])
                
                # Find first relevant item
                for rank, item in enumerate(recommended_items, 1):
                    if item in interactions:
                        reciprocal_ranks.append(1.0 / rank)
                        break
            
            return float(np.mean(reciprocal_ranks)) if reciprocal_ranks else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating MRR: {str(e)}")
            return 0.0
    
    def _calculate_arhr_at_k(self,
                            recommendations: List[Dict[str, Any]],
                            k: int) -> float:
        """Calculate Average Reciprocal Hit Rank at k."""
        try:
            if not recommendations:
                return 0.0
            
            arhr_scores = []
            for rec in recommendations:
                user_id = rec['user_id']
                recommended_items = rec['items'][:k]
                
                # Get user interactions after recommendation
                interactions = self._get_user_interactions_after(user_id, rec['timestamp'])
                
                # Calculate reciprocal ranks for all hits
                reciprocal_ranks = [
                    1.0 / (rank + 1)
                    for rank, item in enumerate(recommended_items)
                    if item in interactions
                ]
                
                if reciprocal_ranks:
                    arhr_scores.append(np.mean(reciprocal_ranks))
            
            return float(np.mean(arhr_scores)) if arhr_scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating ARHR@{k}: {str(e)}")
            return 0.0
    
    def _calculate_rank_correlation(self, recommendations: List[Dict[str, Any]]) -> float:
        """Calculate rank correlation between predicted and actual user preferences."""
        try:
            if not recommendations:
                return 0.0
            
            correlations = []
            for rec in recommendations:
                user_id = rec['user_id']
                recommended_items = rec['items']
                scores = rec['scores']
                
                # Get user interactions after recommendation
                interactions = self._get_user_interactions_after(user_id, rec['timestamp'])
                if not interactions:
                    continue
                
                # Create ranking dictionaries
                pred_ranks = {item: -score for item, score in zip(recommended_items, scores)}
                actual_ranks = {item: -idx for idx, item in enumerate(interactions)}
                
                # Calculate correlation for common items
                common_items = set(pred_ranks.keys()) & set(actual_ranks.keys())
                if common_items:
                    pred_values = [pred_ranks[item] for item in common_items]
                    actual_values = [actual_ranks[item] for item in common_items]
                    correlation = np.corrcoef(pred_values, actual_values)[0, 1]
                    if not np.isnan(correlation):
                        correlations.append(correlation)
            
            return float(np.mean(correlations)) if correlations else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating rank correlation: {str(e)}")
            return 0.0
    
    def _calculate_diversity_metrics(self, recommendations: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate diversity-based metrics."""
        try:
            metrics = {
                'item_coverage': self._calculate_item_coverage(recommendations),
                'user_coverage': self._calculate_user_coverage(recommendations),
                'category_coverage': self._calculate_category_coverage(recommendations),
                'diversity_score': self._calculate_diversity_score(recommendations),
                'serendipity': self._calculate_serendipity(recommendations)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating diversity metrics: {str(e)}")
            return {}
    
    def _calculate_item_coverage(self, recommendations: List[Dict[str, Any]]) -> float:
        """Calculate item coverage ratio."""
        try:
            if not recommendations:
                return 0.0
            
            # Get all recommended items
            recommended_items = set()
            for rec in recommendations:
                recommended_items.update(rec['items'])
            
            # Get total number of items in the system
            total_items = self._get_total_items()
            
            return float(len(recommended_items) / total_items) if total_items > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating item coverage: {str(e)}")
            return 0.0
    
    def _calculate_user_coverage(self, recommendations: List[Dict[str, Any]]) -> float:
        """Calculate user coverage ratio."""
        try:
            if not recommendations:
                return 0.0
            
            # Get unique users who received recommendations
            recommended_users = set(rec['user_id'] for rec in recommendations)
            
            # Get total number of active users
            total_users = len(self.interaction_tracker.interactions)
            
            return float(len(recommended_users) / total_users) if total_users > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating user coverage: {str(e)}")
            return 0.0
    
    def _calculate_category_coverage(self, recommendations: List[Dict[str, Any]]) -> float:
        """Calculate category coverage ratio."""
        try:
            if not recommendations:
                return 0.0
            
            # Get categories from metadata
            recommended_categories = set()
            for rec in recommendations:
                metadata = rec.get('metadata', {})
                categories = metadata.get('categories', [])
                recommended_categories.update(categories)
            
            # Get total number of categories
            total_categories = self._get_total_categories()
            
            return float(len(recommended_categories) / total_categories) if total_categories > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating category coverage: {str(e)}")
            return 0.0
    
    def _calculate_diversity_score(self, recommendations: List[Dict[str, Any]]) -> float:
        """Calculate recommendation diversity score."""
        try:
            if not recommendations:
                return 0.0
            
            diversity_scores = []
            for rec in recommendations:
                items = rec['items']
                metadata = rec.get('metadata', {})
                categories = metadata.get('categories', [])
                
                if categories:
                    # Calculate category diversity
                    category_counts = pd.Series(categories).value_counts(normalize=True)
                    entropy = -np.sum(category_counts * np.log2(category_counts))
                    max_entropy = np.log2(len(category_counts))
                    diversity = entropy / max_entropy if max_entropy > 0 else 0
                    diversity_scores.append(diversity)
            
            return float(np.mean(diversity_scores)) if diversity_scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating diversity score: {str(e)}")
            return 0.0
    
    def _calculate_serendipity(self, recommendations: List[Dict[str, Any]]) -> float:
        """Calculate serendipity score."""
        try:
            if not recommendations:
                return 0.0
            
            serendipity_scores = []
            for rec in recommendations:
                user_id = rec['user_id']
                recommended_items = set(rec['items'])
                
                # Get user's previous interactions
                previous_interactions = self._get_user_interactions_before(user_id, rec['timestamp'])
                previous_categories = self._get_item_categories(previous_interactions)
                
                # Get categories of recommended items
                recommended_categories = self._get_item_categories(recommended_items)
                
                # Calculate novelty score
                if previous_categories and recommended_categories:
                    novelty = 1 - len(previous_categories & recommended_categories) / len(recommended_categories)
                    serendipity_scores.append(novelty)
            
            return float(np.mean(serendipity_scores)) if serendipity_scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating serendipity: {str(e)}")
            return 0.0
    
    def _calculate_temporal_metrics(self, recommendations: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate temporal performance metrics."""
        try:
            metrics = {
                'responsiveness': self._calculate_responsiveness(recommendations),
                'freshness': self._calculate_freshness(recommendations),
                'temporal_diversity': self._calculate_temporal_diversity(recommendations)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating temporal metrics: {str(e)}")
            return {}
    
    def _calculate_business_metrics(self, recommendations: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate business-related metrics."""
        try:
            metrics = {
                'conversion_rate': self._calculate_conversion_rate(recommendations),
                'revenue_impact': self._calculate_revenue_impact(recommendations),
                'user_satisfaction': self._calculate_user_satisfaction(recommendations)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating business metrics: {str(e)}")
            return {}
    
    def _get_user_interactions_after(self,
                                    user_id: int,
                                    timestamp: datetime) -> Set[int]:
        """Get user interactions after a specific timestamp."""
        try:
            interactions = self.interaction_tracker.interactions.get(user_id, [])
            return set(
                interaction['item_id']
                for interaction in interactions
                if interaction['timestamp'] > timestamp
            )
            
        except Exception as e:
            logger.error(f"Error getting user interactions after timestamp: {str(e)}")
            return set()
    
    def _get_user_interactions_before(self,
                                     user_id: int,
                                     timestamp: datetime) -> Set[int]:
        """Get user interactions before a specific timestamp."""
        try:
            interactions = self.interaction_tracker.interactions.get(user_id, [])
            return set(
                interaction['item_id']
                for interaction in interactions
                if interaction['timestamp'] < timestamp
            )
            
        except Exception as e:
            logger.error(f"Error getting user interactions before timestamp: {str(e)}")
            return set()
    
    def _get_total_items(self) -> int:
        """Get total number of items in the system."""
        try:
            # This should be implemented based on your data structure
            return 1000  # Placeholder
            
        except Exception as e:
            logger.error(f"Error getting total items: {str(e)}")
            return 0
    
    def _get_total_categories(self) -> int:
        """Get total number of categories in the system."""
        try:
            # This should be implemented based on your data structure
            return 100  # Placeholder
            
        except Exception as e:
            logger.error(f"Error getting total categories: {str(e)}")
            return 0
    
    def _get_item_categories(self, items: Set[int]) -> Set[str]:
        """Get categories for a set of items."""
        try:
            # This should be implemented based on your data structure
            return set()  # Placeholder
            
        except Exception as e:
            logger.error(f"Error getting item categories: {str(e)}")
            return set()
    
    def _update_metrics_history(self, metrics: Dict[str, Any]) -> None:
        """Update metrics history with current calculations."""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Flatten metrics dictionary
            flat_metrics = self._flatten_dict(metrics)
            
            # Store in history
            self.metrics_history[timestamp] = flat_metrics
            
        except Exception as e:
            logger.error(f"Error updating metrics history: {str(e)}")
    
    def _flatten_dict(self,
                      d: Dict[str, Any],
                      parent_key: str = '',
                      sep: str = '.') -> Dict[str, float]:
        """Flatten a nested dictionary."""
        try:
            items: List[Tuple[str, float]] = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                
                if isinstance(v, dict):
                    items.extend(self._flatten_dict(v, new_key, sep).items())
                else:
                    items.append((new_key, float(v)))
            
            return dict(items)
            
        except Exception as e:
            logger.error(f"Error flattening dictionary: {str(e)}")
            return {}