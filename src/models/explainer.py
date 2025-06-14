import numpy as np
import pandas as pd
import shap
import logging
from typing import Dict, List, Tuple, Any, Optional
from sklearn.preprocessing import StandardScaler
from src.models.hybrid_recommender import HybridRecommender

logger = logging.getLogger(__name__)

class RecommendationExplainer:
    def __init__(self, model: HybridRecommender):
        if not isinstance(model, HybridRecommender):
            raise ValueError("Model must be an instance of HybridRecommender")
        self.model = model
        self.content_explainer = None
        self.collab_explainer = None
        
    def _prepare_content_features(self, book_title: str) -> Tuple[np.ndarray, List[str]]:
        """Prepare content features for explanation."""
        try:
            if not isinstance(book_title, str) or not book_title.strip():
                raise ValueError("Book title must be a non-empty string")

            tfidf_matrix = self.model.content_recommender.tfidf_matrix
            feature_names = self.model.content_recommender.tfidf.get_feature_names_out()
            
            if book_title not in self.model.content_recommender.book_indices:
                raise KeyError(f"Book title '{book_title}' not found in the database")
                
            book_idx = self.model.content_recommender.book_indices[book_title]
            feature_vector = tfidf_matrix[book_idx].toarray()
            
            return feature_vector, feature_names
            
        except Exception as e:
            logger.error(f"Error preparing content features: {str(e)}", exc_info=True)
            raise
    
    def _prepare_collaborative_features(self, user_id: int) -> Tuple[np.ndarray, List[str]]:
        """Prepare collaborative filtering features for explanation."""
        try:
            if not isinstance(user_id, (int, np.integer)) or user_id < 0:
                raise ValueError("User ID must be a non-negative integer")

            if user_id >= len(self.model.collab_recommender.user_factors):
                raise ValueError(f"User ID {user_id} not found in the database")

            user_factors = self.model.collab_recommender.user_factors[user_id]
            feature_names = [f"Factor_{i+1}" for i in range(len(user_factors))]
            
            return user_factors.reshape(1, -1), feature_names
            
        except Exception as e:
            logger.error(f"Error preparing collaborative features: {str(e)}", exc_info=True)
            raise
    
    def explain_content_based(self, book_title: str, n_features: int = 10) -> Dict[str, Any]:
        """Explain content-based recommendations using SHAP values."""
        try:
            if n_features <= 0:
                raise ValueError("Number of features must be positive")

            feature_vector, feature_names = self._prepare_content_features(book_title)
            
            if self.content_explainer is None:
                background = self.model.content_recommender.tfidf_matrix[:min(100, len(self.model.content_recommender.tfidf_matrix))].toarray()
                self.content_explainer = shap.KernelExplainer(
                    self.model.content_recommender.get_similar_books,
                    background
                )
            
            shap_values = self.content_explainer.shap_values(feature_vector)
            if not isinstance(shap_values, np.ndarray):
                raise ValueError("Invalid SHAP values returned")

            feature_importance = np.abs(shap_values).mean(0)
            top_indices = np.argsort(feature_importance)[-min(n_features, len(feature_importance)):]
            
            return {
                'top_features': [
                    {
                        'feature': feature_names[i],
                        'importance': float(feature_importance[i]),
                        'value': float(feature_vector[0][i]),
                        'shap_value': float(shap_values[0][i])
                    }
                    for i in top_indices
                ],
                'overall_impact': float(np.abs(shap_values).sum())
            }
            
        except Exception as e:
            logger.error(f"Error explaining content-based recommendations: {str(e)}", exc_info=True)
            raise
    
    def explain_collaborative(self, user_id: int, n_factors: int = 5) -> Dict[str, Any]:
        """Explain collaborative filtering recommendations using SHAP values."""
        try:
            if n_factors <= 0:
                raise ValueError("Number of factors must be positive")

            user_factors, factor_names = self._prepare_collaborative_features(user_id)
            
            if self.collab_explainer is None:
                background = self.model.collab_recommender.user_factors[:min(100, len(self.model.collab_recommender.user_factors))]
                self.collab_explainer = shap.KernelExplainer(
                    self.model.collab_recommender.predict,
                    background
                )
            
            shap_values = self.collab_explainer.shap_values(user_factors)
            if not isinstance(shap_values, np.ndarray):
                raise ValueError("Invalid SHAP values returned")

            factor_importance = np.abs(shap_values).mean(0)
            top_indices = np.argsort(factor_importance)[-min(n_factors, len(factor_importance)):]
            
            return {
                'top_factors': [
                    {
                        'factor': factor_names[i],
                        'importance': float(factor_importance[i]),
                        'value': float(user_factors[0][i]),
                        'shap_value': float(shap_values[0][i])
                    }
                    for i in top_indices
                ],
                'overall_impact': float(np.abs(shap_values).sum())
            }
            
        except Exception as e:
            logger.error(f"Error explaining collaborative recommendations: {str(e)}", exc_info=True)
            raise
    
    def explain_hybrid_recommendation(self, user_id: Optional[int], book_title: str) -> Dict[str, Any]:
        """Provide comprehensive explanation for hybrid recommendations."""
        try:
            if not isinstance(book_title, str) or not book_title.strip():
                raise ValueError("Book title must be a non-empty string")

            content_based_explanation = self.explain_content_based(book_title)
            collaborative_explanation = self.explain_collaborative(user_id) if user_id is not None else None

            explanations = {
                'content_based': content_based_explanation,
                'collaborative': collaborative_explanation,
                'hybrid_weights': {
                    'content_weight': self.model.content_weight,
                    'collaborative_weight': 1 - self.model.content_weight
                }
            }
            
            content_impact = content_based_explanation['overall_impact']
            collab_impact = collaborative_explanation['overall_impact'] if collaborative_explanation else 0
            
            weighted_score = float(self.model.content_weight * content_impact + 
                                 (1 - self.model.content_weight) * collab_impact)
            
            explanations['overall_confidence'] = {
                'score': weighted_score,
                'interpretation': self._interpret_confidence_score(
                    content_impact, collab_impact, self.model.content_weight
                )
            }
            
            return explanations
            
        except Exception as e:
            logger.error(f"Error explaining hybrid recommendations: {str(e)}", exc_info=True)
            raise
    
    def _interpret_confidence_score(self, content_impact: float, collab_impact: float, content_weight: float) -> str:
        """Interpret the confidence score for recommendations."""
        try:
            if not all(isinstance(x, (int, float)) for x in [content_impact, collab_impact, content_weight]):
                raise ValueError("All inputs must be numeric")
            if not 0 <= content_weight <= 1:
                raise ValueError("Content weight must be between 0 and 1")

            weighted_score = content_weight * content_impact + (1 - content_weight) * collab_impact
            
            confidence_levels = [
                (0.8, "Very High Confidence"),
                (0.6, "High Confidence"),
                (0.4, "Moderate Confidence"),
                (0.2, "Low Confidence"),
                (0.0, "Very Low Confidence")
            ]
            
            for threshold, level in confidence_levels:
                if weighted_score > threshold:
                    return level
            return "Very Low Confidence"
                
        except Exception as e:
            logger.error(f"Error interpreting confidence score: {str(e)}", exc_info=True)
            return "Unable to determine confidence"
    
    def generate_explanation_summary(self, explanation: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the recommendation explanation."""
        try:
            if not isinstance(explanation, dict):
                raise ValueError("Explanation must be a dictionary")

            summary = ["Here's why we recommended this book:"]
            
            if explanation.get('content_based'):
                summary.append("\nBased on book content:")
                for feature in explanation['content_based']['top_features'][:3]:
                    summary.append(f"- Similar {feature['feature']} content")
            
            if explanation.get('collaborative'):
                summary.append("\nBased on user preferences:")
                for factor in explanation['collaborative']['top_factors'][:3]:
                    summary.append(f"- Strong alignment with {factor['factor']}")
            
            if 'overall_confidence' in explanation:
                summary.append(f"\nOverall Recommendation Confidence: {explanation['overall_confidence']['interpretation']}")
            
            return '\n'.join(summary)
            
        except Exception as e:
            logger.error(f"Error generating explanation summary: {str(e)}", exc_info=True)
            return "Unable to generate explanation summary"
