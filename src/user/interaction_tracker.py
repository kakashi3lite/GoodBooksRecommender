import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from collections import defaultdict
from src.config import Config

logger = logging.getLogger(__name__)

class InteractionTracker:
    def __init__(self, config: Config):
        """Initialize the interaction tracker with configuration."""
        self.config = config
        self.interactions: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        self.session_data: Dict[str, Dict[str, Any]] = {}
        self.feedback_metrics: Dict[str, List[float]] = defaultdict(list)
        self.engagement_scores: Dict[int, float] = {}
        self.interaction_weights = {
            'view': 1,
            'click': 2,
            'rate': 3,
            'review': 4,
            'purchase': 5,
            'share': 3,
            'add_to_wishlist': 2,
            'complete_reading': 4
        }
        
    def track_interaction(self, 
                         user_id: int,
                         interaction_type: str,
                         book_id: int,
                         metadata: Dict[str, Any],
                         session_id: Optional[str] = None) -> Dict[str, Any]:
        """Track a user interaction with a book."""
        if not isinstance(user_id, int) or user_id < 0:
            raise ValueError("Invalid user_id")
        if not isinstance(book_id, int) or book_id < 0:
            raise ValueError("Invalid book_id")
            
        interaction = {
            'user_id': user_id,
            'book_id': book_id,
            'type': interaction_type,
            'timestamp': datetime.now(),
            'metadata': metadata,
            'session_id': session_id
        }
        
        try:
            self.interactions[user_id].append(interaction)
            
            if session_id:
                self._update_session_data(session_id, interaction)
            
            self._update_engagement_score(user_id, interaction_type)
            
            logger.info(f"Tracked {interaction_type} interaction for user {user_id}")
            return interaction
            
        except Exception as e:
            logger.error(f"Error tracking interaction: {str(e)}", exc_info=True)
            raise
    
    def _update_session_data(self, session_id: str, interaction: Dict[str, Any]) -> None:
        """Update session-level interaction data."""
        if not session_id:
            raise ValueError("Invalid session_id")
            
        try:
            if session_id not in self.session_data:
                self.session_data[session_id] = {
                    'start_time': interaction['timestamp'],
                    'interactions': [],
                    'metrics': defaultdict(float)
                }
            
            session = self.session_data[session_id]
            session['interactions'].append(interaction)
            session['last_activity'] = interaction['timestamp']
            
            self._update_session_metrics(session, interaction)
            
        except Exception as e:
            logger.error(f"Error updating session data: {str(e)}", exc_info=True)
            raise
    
    def _update_session_metrics(self, session: Dict[str, Any], interaction: Dict[str, Any]) -> None:
        """Update metrics for the current session."""
        try:
            metrics = session['metrics']
            interaction_type = interaction['type']
            
            metrics[f"count_{interaction_type}"] += 1
            
            if duration := interaction['metadata'].get('duration'):
                metrics['total_engagement_time'] += float(duration)
            
            if interaction_type == 'purchase':
                metrics['conversions'] += 1
            elif interaction_type == 'add_to_wishlist':
                metrics['wishlist_adds'] += 1
            
            metrics['session_duration'] = (
                interaction['timestamp'] - session['start_time']
            ).total_seconds()
            
        except Exception as e:
            logger.error(f"Error updating session metrics: {str(e)}", exc_info=True)
            raise
    
    def _update_engagement_score(self, user_id: int, interaction_type: str) -> None:
        """Update user engagement score based on interaction type."""
        try:
            current_score = self.engagement_scores.get(user_id, 0)
            
            user_interactions = self.interactions[user_id]
            if len(user_interactions) > 1:
                last_interaction = max(
                    (int_data['timestamp'] for int_data in user_interactions[:-1]),
                    default=datetime.now()
                )
                days_since_last = (datetime.now() - last_interaction).days
                decayed_score = current_score * (0.95 ** days_since_last)
            else:
                decayed_score = current_score
            
            interaction_weight = self.interaction_weights.get(interaction_type, 1)
            new_score = decayed_score + interaction_weight
            
            self.engagement_scores[user_id] = min(100, new_score)
            
        except Exception as e:
            logger.error(f"Error updating engagement score: {str(e)}", exc_info=True)
            raise
    
    def record_feedback(self,
                       user_id: int,
                       book_id: int,
                       feedback_type: str,
                       rating: float,
                       metadata: Dict[str, Any]) -> None:
        """Record user feedback for a book."""
        if not (0 <= rating <= 5):
            raise ValueError("Rating must be between 0 and 5")
            
        try:
            feedback = {
                'user_id': user_id,
                'book_id': book_id,
                'type': feedback_type,
                'rating': rating,
                'timestamp': datetime.now(),
                'metadata': metadata
            }
            
            self.track_interaction(
                user_id=user_id,
                interaction_type=feedback_type,
                book_id=book_id,
                metadata=metadata
            )
            
            metric_key = f"{feedback_type}_rating"
            self.feedback_metrics[metric_key].append(rating)
            
            logger.info(f"Recorded {feedback_type} feedback for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error recording feedback: {str(e)}", exc_info=True)
            raise
    
    def get_user_statistics(self, user_id: int, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get statistics for a user's interactions and feedback."""
        if user_id not in self.interactions:
            return {}
            
        try:
            interactions = self.interactions[user_id]
            
            if time_window:
                cutoff_time = datetime.now() - time_window
                interactions = [i for i in interactions if i['timestamp'] >= cutoff_time]
            
            if not interactions:
                return {'total_interactions': 0}
                
            interaction_counts = defaultdict(int)
            for interaction in interactions:
                interaction_counts[interaction['type']] += 1
            
            ratings = [
                i['metadata'].get('rating', 0) for i in interactions 
                if 'rating' in i['metadata'] and isinstance(i['metadata']['rating'], (int, float))
            ]
            
            return {
                'total_interactions': len(interactions),
                'interaction_counts': dict(interaction_counts),
                'average_rating': float(np.mean(ratings)) if ratings else 0,
                'engagement_score': self.engagement_scores.get(user_id, 0),
                'last_interaction': max(i['timestamp'] for i in interactions)
            }
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {str(e)}", exc_info=True)
            raise
    
    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a specific session."""
        if not session_id or session_id not in self.session_data:
            return {}
            
        try:
            session = self.session_data[session_id]
            interaction_count = len(session['interactions'])
            
            return {
                'duration': session['metrics']['session_duration'],
                'interaction_count': interaction_count,
                'engagement_time': session['metrics'].get('total_engagement_time', 0),
                'conversion_rate': (session['metrics'].get('conversions', 0) / interaction_count) 
                                 if interaction_count > 0 else 0,
                'start_time': session['start_time'],
                'last_activity': session['last_activity']
            }
            
        except Exception as e:
            logger.error(f"Error getting session statistics: {str(e)}", exc_info=True)
            raise
    
    def analyze_feedback_trends(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Analyze trends in user feedback over time."""
        try:
            trends = {}
            
            for metric_key, values in self.feedback_metrics.items():
                if not values:
                    continue
                    
                values_array = np.array(values)
                if not np.isfinite(values_array).all():
                    logger.warning(f"Non-finite values found in {metric_key}")
                    continue
                
                trends[metric_key] = {
                    'average': float(np.mean(values_array)),
                    'trend': self._calculate_trend(values_array),
                    'distribution': self._calculate_distribution(values_array)
                }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing feedback trends: {str(e)}", exc_info=True)
            raise
    
    def _calculate_trend(self, values: Union[List[float], np.ndarray]) -> Dict[str, float]:
        """Calculate trend metrics for a series of values."""
        try:
            if len(values) < 2:
                return {'slope': 0.0, 'change_rate': 0.0}
            
            x = np.arange(len(values))
            slope, _ = np.polyfit(x, values, 1)
            
            change_rate = (float(values[-1]) - float(values[0])) / float(values[0]) if values[0] != 0 else 0.0
            
            return {
                'slope': float(slope),
                'change_rate': float(change_rate)
            }
            
        except Exception as e:
            logger.error(f"Error calculating trend: {str(e)}", exc_info=True)
            raise
    
    def _calculate_distribution(self, values: Union[List[float], np.ndarray]) -> Dict[str, Any]:
        """Calculate distribution statistics for values."""
        try:
            return {
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'median': float(np.median(values)),
                'std': float(np.std(values)),
                'quartiles': [float(q) for q in np.percentile(values, [25, 50, 75])]
            }
            
        except Exception as e:
            logger.error(f"Error calculating distribution: {str(e)}", exc_info=True)
            raise