import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from src.models.hybrid_recommender import HybridRecommender
from src.models.model_manager import ModelManager
from src.data.data_loader import DataLoader
from src.config import Config

logger = logging.getLogger(__name__)

class ModelUpdater:
    def __init__(self, config: Config):
        self.config = config
        self.model_manager = ModelManager(config)
        self.data_loader = DataLoader(config)
        self.current_model: Optional[HybridRecommender] = None
        self.performance_metrics: Dict[str, float] = {}
        
    def load_current_model(self) -> None:
        """Load the currently deployed model."""
        try:
            self.current_model = self.model_manager.load_latest_model()
            logger.info("Successfully loaded current model")
        except Exception as e:
            logger.error(f"Error loading current model: {str(e)}")
            raise
    
    def evaluate_model(self, model: HybridRecommender, test_data: Tuple[np.ndarray, np.ndarray]) -> Dict[str, float]:
        """Evaluate model performance on test data."""
        try:
            X_test, y_test = test_data
            predictions = model.predict(X_test)
            
            # Calculate various metrics
            metrics = {
                'mse': np.mean((y_test - predictions) ** 2),
                'rmse': np.sqrt(np.mean((y_test - predictions) ** 2)),
                'mae': np.mean(np.abs(y_test - predictions))
            }
            
            # Calculate recommendation quality metrics
            metrics.update(self._calculate_recommendation_metrics(model, X_test, y_test))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            raise
    
    def _calculate_recommendation_metrics(self, model: HybridRecommender, 
                                        X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Calculate recommendation-specific metrics."""
        try:
            metrics = {}
            
            # Precision@K and Recall@K
            for k in [5, 10, 20]:
                precision, recall = self._calculate_precision_recall_at_k(model, X_test, y_test, k)
                metrics[f'precision@{k}'] = precision
                metrics[f'recall@{k}'] = recall
            
            # Diversity score
            metrics['diversity'] = self._calculate_diversity_score(model)
            
            # Coverage score
            metrics['coverage'] = self._calculate_coverage_score(model)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating recommendation metrics: {str(e)}")
            raise
    
    def _calculate_precision_recall_at_k(self, model: HybridRecommender, 
                                        X_test: np.ndarray, y_test: np.ndarray, 
                                        k: int) -> Tuple[float, float]:
        """Calculate precision and recall at K."""
        try:
            # Get top-K recommendations for each user
            user_ids = np.unique(X_test[:, 0])
            precision_scores = []
            recall_scores = []
            
            for user_id in user_ids:
                # Get actual positive items (ratings >= 4)
                user_mask = X_test[:, 0] == user_id
                actual_positives = set(X_test[user_mask & (y_test >= 4)][:, 1])
                
                if not actual_positives:
                    continue
                
                # Get recommended items
                recommended = set(model.get_recommendations(user_id, k)['book_id'].values)
                
                # Calculate metrics
                true_positives = len(actual_positives.intersection(recommended))
                precision = true_positives / k
                recall = true_positives / len(actual_positives)
                
                precision_scores.append(precision)
                recall_scores.append(recall)
            
            return np.mean(precision_scores), np.mean(recall_scores)
            
        except Exception as e:
            logger.error(f"Error calculating precision/recall: {str(e)}")
            raise
    
    def _calculate_diversity_score(self, model: HybridRecommender) -> float:
        """Calculate recommendation diversity score."""
        try:
            # Sample users for diversity calculation
            sample_users = np.random.choice(
                list(model.collab_recommender.user_factors.keys()),
                min(100, len(model.collab_recommender.user_factors)),
                replace=False
            )
            
            unique_items = set()
            total_items = 0
            
            for user_id in sample_users:
                recs = model.get_recommendations(user_id, 10)['book_id'].values
                unique_items.update(recs)
                total_items += len(recs)
            
            return len(unique_items) / total_items
            
        except Exception as e:
            logger.error(f"Error calculating diversity score: {str(e)}")
            raise
    
    def _calculate_coverage_score(self, model: HybridRecommender) -> float:
        """Calculate catalog coverage score."""
        try:
            # Sample users for coverage calculation
            sample_users = np.random.choice(
                list(model.collab_recommender.user_factors.keys()),
                min(1000, len(model.collab_recommender.user_factors)),
                replace=False
            )
            
            recommended_items = set()
            all_items = set(model.content_recommender.book_indices.values())
            
            for user_id in sample_users:
                recs = model.get_recommendations(user_id, 20)['book_id'].values
                recommended_items.update(recs)
            
            return len(recommended_items) / len(all_items)
            
        except Exception as e:
            logger.error(f"Error calculating coverage score: {str(e)}")
            raise
    
    def should_retrain(self, new_data_metrics: Dict[str, float]) -> bool:
        """Determine if model retraining is needed based on performance metrics."""
        try:
            if not self.performance_metrics:
                return True
            
            # Define thresholds for different metrics
            thresholds = {
                'rmse': 0.05,  # 5% degradation in RMSE
                'precision@10': 0.1,  # 10% degradation in precision
                'diversity': 0.1,  # 10% degradation in diversity
                'coverage': 0.1  # 10% degradation in coverage
            }
            
            # Check for significant degradation in any metric
            for metric, threshold in thresholds.items():
                if metric in new_data_metrics and metric in self.performance_metrics:
                    degradation = (self.performance_metrics[metric] - new_data_metrics[metric]) \
                                 / self.performance_metrics[metric]
                    if degradation > threshold:
                        logger.info(f"Retraining triggered due to {metric} degradation of {degradation:.2%}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking retraining condition: {str(e)}")
            return True
    
    def update_model(self) -> None:
        """Update the model if necessary based on new data and performance."""
        try:
            # Load and prepare new data
            logger.info("Loading new data for model update check")
            new_data = self.data_loader.load_datasets()
            
            # Load current model if not loaded
            if self.current_model is None:
                self.load_current_model()
            
            # Evaluate current model on new data
            new_data_metrics = self.evaluate_model(self.current_model, new_data)
            
            if self.should_retrain(new_data_metrics):
                logger.info("Starting model retraining process")
                
                # Train new model
                new_model = HybridRecommender(self.config)
                new_model.fit(new_data[0], new_data[1])
                
                # Evaluate new model
                new_model_metrics = self.evaluate_model(new_model, new_data)
                
                # Save new model if it performs better
                if new_model_metrics['rmse'] < new_data_metrics['rmse']:
                    logger.info("New model performs better, saving and updating metrics")
                    self.model_manager.save_model(
                        new_model,
                        metrics=new_model_metrics,
                        metadata={
                            'training_date': datetime.now().isoformat(),
                            'data_size': len(new_data[0]),
                            'improvement': {
                                metric: f"{(new_data_metrics[metric] - value):.4f}"
                                for metric, value in new_model_metrics.items()
                            }
                        }
                    )
                    self.current_model = new_model
                    self.performance_metrics = new_model_metrics
                else:
                    logger.info("New model does not show improvement, keeping current model")
            else:
                logger.info("Model retraining not needed at this time")
                
        except Exception as e:
            logger.error(f"Error during model update process: {str(e)}")
            raise