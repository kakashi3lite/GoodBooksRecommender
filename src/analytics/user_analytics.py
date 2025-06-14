import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from src.config import Config
from src.user.interaction_tracker import InteractionTracker
from src.user.profile_manager import UserProfileManager

logger = logging.getLogger(__name__)

class UserAnalytics:
    def __init__(self, 
                 config: Config,
                 interaction_tracker: InteractionTracker,
                 profile_manager: UserProfileManager):
        self.config = config
        self.interaction_tracker = interaction_tracker
        self.profile_manager = profile_manager
        self.user_segments: Dict[str, List[int]] = defaultdict(list)
        self.cohort_metrics: Dict[str, Dict[str, float]] = {}
        self.retention_data: Dict[str, Dict[int, float]] = {}
        
    def analyze_user_behavior(self, user_id: int, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Analyze user behavior patterns and preferences."""
        try:
            # Get user interactions and profile data
            interactions = self.interaction_tracker.get_user_statistics(user_id, time_window)
            profile = self.profile_manager.get_user_preferences(user_id)
            
            # Calculate behavior metrics
            analysis = {
                'engagement_metrics': self._calculate_engagement_metrics(interactions),
                'preference_analysis': self._analyze_preferences(profile),
                'interaction_patterns': self._analyze_interaction_patterns(user_id, time_window),
                'recommendation_effectiveness': self._analyze_recommendation_effectiveness(user_id),
                'user_segment': self._determine_user_segment(user_id)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing user behavior: {str(e)}")
            raise
    
    def _calculate_engagement_metrics(self, interactions: Dict[str, Any]) -> Dict[str, float]:
        """Calculate user engagement metrics."""
        try:
            total_interactions = interactions['total_interactions']
            if total_interactions == 0:
                return {'engagement_score': 0.0, 'activity_frequency': 0.0, 'conversion_rate': 0.0}
            
            # Calculate metrics
            metrics = {
                'engagement_score': float(interactions['engagement_score']),
                'activity_frequency': self._calculate_activity_frequency(interactions),
                'conversion_rate': self._calculate_conversion_rate(interactions),
                'average_session_depth': self._calculate_session_depth(interactions),
                'retention_score': self._calculate_retention_score(interactions)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating engagement metrics: {str(e)}")
            raise
    
    def _calculate_activity_frequency(self, interactions: Dict[str, Any]) -> float:
        """Calculate user activity frequency score."""
        try:
            counts = interactions['interaction_counts']
            weights = {
                'view': 1,
                'click': 2,
                'rate': 3,
                'review': 4,
                'purchase': 5
            }
            
            weighted_sum = sum(counts.get(k, 0) * w for k, w in weights.items())
            max_possible = sum(weights.values()) * max(counts.values()) if counts else 1
            
            return weighted_sum / max_possible if max_possible > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating activity frequency: {str(e)}")
            return 0.0
    
    def _calculate_conversion_rate(self, interactions: Dict[str, Any]) -> float:
        """Calculate user conversion rate."""
        try:
            counts = interactions['interaction_counts']
            views = counts.get('view', 0)
            purchases = counts.get('purchase', 0)
            
            return purchases / views if views > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating conversion rate: {str(e)}")
            return 0.0
    
    def _calculate_session_depth(self, interactions: Dict[str, Any]) -> float:
        """Calculate average session depth."""
        try:
            counts = interactions['interaction_counts']
            total_sessions = counts.get('session', 1)  # Avoid division by zero
            total_interactions = sum(counts.values())
            
            return total_interactions / total_sessions
            
        except Exception as e:
            logger.error(f"Error calculating session depth: {str(e)}")
            return 0.0
    
    def _calculate_retention_score(self, interactions: Dict[str, Any]) -> float:
        """Calculate user retention score."""
        try:
            if not interactions.get('last_interaction'):
                return 0.0
            
            days_since_last = (datetime.now() - interactions['last_interaction']).days
            frequency = self._calculate_activity_frequency(interactions)
            
            # Exponential decay based on recency and frequency
            retention_score = frequency * np.exp(-0.1 * days_since_last)
            return float(min(1.0, retention_score))
            
        except Exception as e:
            logger.error(f"Error calculating retention score: {str(e)}")
            return 0.0
    
    def _analyze_preferences(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user preferences and their evolution."""
        try:
            preferences = profile.get('genres', {})
            weights = profile.get('weights', {})
            
            analysis = {
                'primary_interests': self._get_top_preferences(preferences, n=3),
                'preference_stability': self._calculate_preference_stability(preferences),
                'diversity_index': self._calculate_preference_diversity(preferences),
                'preference_confidence': self._calculate_preference_confidence(weights)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing preferences: {str(e)}")
            raise
    
    def _get_top_preferences(self, preferences: Dict[str, float], n: int = 3) -> List[Dict[str, Any]]:
        """Get top N user preferences with scores."""
        try:
            sorted_prefs = sorted(preferences.items(), key=lambda x: x[1], reverse=True)
            return [
                {'category': k, 'score': float(v)}
                for k, v in sorted_prefs[:n]
            ]
            
        except Exception as e:
            logger.error(f"Error getting top preferences: {str(e)}")
            return []
    
    def _calculate_preference_stability(self, preferences: Dict[str, float]) -> float:
        """Calculate stability score for user preferences."""
        try:
            if not preferences:
                return 0.0
            
            # Calculate variance in preference scores
            scores = list(preferences.values())
            variance = np.var(scores) if len(scores) > 1 else 0
            
            # Convert variance to stability score (inverse relationship)
            stability = 1 / (1 + variance)
            return float(stability)
            
        except Exception as e:
            logger.error(f"Error calculating preference stability: {str(e)}")
            return 0.0
    
    def _calculate_preference_diversity(self, preferences: Dict[str, float]) -> float:
        """Calculate diversity index for user preferences."""
        try:
            if not preferences:
                return 0.0
            
            # Calculate Shannon diversity index
            total = sum(preferences.values())
            proportions = [v/total for v in preferences.values()]
            diversity = -sum(p * np.log(p) for p in proportions if p > 0)
            
            # Normalize to 0-1 range
            max_diversity = np.log(len(preferences)) if len(preferences) > 0 else 1
            return float(diversity / max_diversity if max_diversity > 0 else 0)
            
        except Exception as e:
            logger.error(f"Error calculating preference diversity: {str(e)}")
            return 0.0
    
    def _calculate_preference_confidence(self, weights: Dict[str, float]) -> float:
        """Calculate confidence score for preference predictions."""
        try:
            if not weights:
                return 0.0
            
            # Weight the confidence based on data sources
            confidence_weights = {
                'explicit_preferences': 1.0,
                'implicit_feedback': 0.8,
                'collaborative_signal': 0.6
            }
            
            weighted_confidence = sum(
                weights.get(k, 0) * w
                for k, w in confidence_weights.items()
            )
            
            return float(min(1.0, weighted_confidence))
            
        except Exception as e:
            logger.error(f"Error calculating preference confidence: {str(e)}")
            return 0.0
    
    def _analyze_interaction_patterns(self, user_id: int, time_window: Optional[timedelta]) -> Dict[str, Any]:
        """Analyze patterns in user interactions."""
        try:
            interactions = self.interaction_tracker.interactions.get(user_id, [])
            if not interactions:
                return {}
            
            # Filter by time window if specified
            if time_window:
                cutoff_time = datetime.now() - time_window
                interactions = [i for i in interactions if i['timestamp'] >= cutoff_time]
            
            patterns = {
                'temporal_patterns': self._analyze_temporal_patterns(interactions),
                'session_patterns': self._analyze_session_patterns(interactions),
                'content_patterns': self._analyze_content_patterns(interactions)
            }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing interaction patterns: {str(e)}")
            raise
    
    def _analyze_temporal_patterns(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal patterns in user interactions."""
        try:
            timestamps = [i['timestamp'] for i in interactions]
            hours = [t.hour for t in timestamps]
            days = [t.weekday() for t in timestamps]
            
            return {
                'peak_hours': self._find_peak_periods(hours, 24),
                'active_days': self._find_peak_periods(days, 7),
                'regularity_score': self._calculate_regularity_score(timestamps)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing temporal patterns: {str(e)}")
            raise
    
    def _find_peak_periods(self, values: List[int], period: int) -> List[int]:
        """Find peak activity periods."""
        try:
            if not values:
                return []
            
            # Count occurrences
            counts = np.bincount(values, minlength=period)
            threshold = np.mean(counts) + np.std(counts)
            
            # Find peaks
            peaks = [i for i, count in enumerate(counts) if count > threshold]
            return peaks
            
        except Exception as e:
            logger.error(f"Error finding peak periods: {str(e)}")
            return []
    
    def _calculate_regularity_score(self, timestamps: List[datetime]) -> float:
        """Calculate regularity score for user activity."""
        try:
            if len(timestamps) < 2:
                return 0.0
            
            # Calculate intervals between activities
            intervals = np.diff([t.timestamp() for t in timestamps])
            
            # Calculate coefficient of variation (lower means more regular)
            cv = np.std(intervals) / np.mean(intervals) if np.mean(intervals) > 0 else float('inf')
            
            # Convert to regularity score (0-1)
            regularity = 1 / (1 + cv)
            return float(regularity)
            
        except Exception as e:
            logger.error(f"Error calculating regularity score: {str(e)}")
            return 0.0
    
    def _analyze_recommendation_effectiveness(self, user_id: int) -> Dict[str, float]:
        """Analyze effectiveness of recommendations for the user."""
        try:
            interactions = self.interaction_tracker.interactions.get(user_id, [])
            recommended_interactions = [
                i for i in interactions
                if i['metadata'].get('recommended', False)
            ]
            
            if not recommended_interactions:
                return {'acceptance_rate': 0.0, 'satisfaction_score': 0.0}
            
            # Calculate metrics
            total_recommended = len(recommended_interactions)
            accepted = sum(1 for i in recommended_interactions if i['type'] in ['click', 'purchase'])
            ratings = [i['metadata'].get('rating', 0) for i in recommended_interactions]
            
            return {
                'acceptance_rate': accepted / total_recommended,
                'satisfaction_score': float(np.mean(ratings)) if ratings else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing recommendation effectiveness: {str(e)}")
            raise
    
    def _determine_user_segment(self, user_id: int) -> str:
        """Determine user segment based on behavior and preferences."""
        try:
            # Get user metrics
            engagement = self.interaction_tracker.engagement_scores.get(user_id, 0)
            interactions = self.interaction_tracker.get_user_statistics(user_id)
            conversion_rate = self._calculate_conversion_rate(interactions)
            
            # Segment determination logic
            if engagement >= 80 and conversion_rate >= 0.1:
                segment = 'power_user'
            elif engagement >= 60:
                segment = 'active_user'
            elif engagement >= 30:
                segment = 'casual_user'
            else:
                segment = 'inactive_user'
            
            # Update segment tracking
            self.user_segments[segment].append(user_id)
            
            return segment
            
        except Exception as e:
            logger.error(f"Error determining user segment: {str(e)}")
            raise