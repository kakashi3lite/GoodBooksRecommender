import numpy as np
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from src.data.data_loader import DataLoader
from src.config import Config

logger = logging.getLogger(__name__)

class UserProfileManager:
    def __init__(self, config: Config):
        self.config = config
        self.data_loader = DataLoader(config)
        self.profiles: Dict[int, Dict[str, Any]] = {}
        self.preference_weights: Dict[int, Dict[str, float]] = {}
        self.interaction_history: Dict[int, List[Dict[str, Any]]] = {}
        
    def create_profile(self, user_id: int, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user profile with initial preferences and metadata."""
        try:
            if user_id in self.profiles:
                raise ValueError(f"Profile already exists for user {user_id}")
            
            profile = {
                'user_id': user_id,
                'created_at': datetime.now(),
                'last_updated': datetime.now(),
                'preferences': self._process_initial_preferences(initial_data.get('preferences', {})),
                'reading_history': [],
                'favorite_genres': initial_data.get('favorite_genres', []),
                'favorite_authors': initial_data.get('favorite_authors', []),
                'reading_level': initial_data.get('reading_level', 'intermediate'),
                'language_preferences': initial_data.get('language_preferences', ['English']),
                'notification_preferences': initial_data.get('notification_preferences', {}),
                'recommendation_settings': self._get_default_recommendation_settings()
            }
            
            self.profiles[user_id] = profile
            self._initialize_preference_weights(user_id)
            
            logger.info(f"Created new profile for user {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error creating user profile: {str(e)}")
            raise
    
    def _process_initial_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate initial user preferences."""
        try:
            processed = {
                'genre_preferences': self._normalize_preferences(preferences.get('genres', {})),
                'topic_preferences': self._normalize_preferences(preferences.get('topics', {})),
                'format_preferences': self._normalize_preferences(preferences.get('formats', {})),
                'length_preference': preferences.get('preferred_length', 'medium'),
                'complexity_preference': preferences.get('preferred_complexity', 'intermediate')
            }
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing preferences: {str(e)}")
            raise
    
    def _normalize_preferences(self, preferences: Dict[str, float]) -> Dict[str, float]:
        """Normalize preference scores to sum to 1."""
        try:
            if not preferences:
                return {}
            
            total = sum(preferences.values())
            if total == 0:
                return preferences
            
            return {k: v/total for k, v in preferences.items()}
            
        except Exception as e:
            logger.error(f"Error normalizing preferences: {str(e)}")
            raise
    
    def _get_default_recommendation_settings(self) -> Dict[str, Any]:
        """Get default recommendation settings for new users."""
        return {
            'diversity_level': 0.3,  # 0-1 scale for recommendation diversity
            'novelty_bias': 0.5,  # 0-1 scale for favoring new vs. popular items
            'serendipity_level': 0.2,  # 0-1 scale for unexpected recommendations
            'content_collaborative_ratio': 0.5,  # Balance between content-based and collaborative filtering
            'max_recommendations': 10,  # Maximum number of recommendations per request
            'exclude_read': True,  # Whether to exclude already read books
            'personalization_strength': 0.7  # 0-1 scale for personalization level
        }
    
    def _initialize_preference_weights(self, user_id: int) -> None:
        """Initialize weights for different preference aspects."""
        try:
            self.preference_weights[user_id] = {
                'explicit_preferences': 0.4,  # Weight for explicitly stated preferences
                'implicit_feedback': 0.3,  # Weight for implicit feedback (reading history)
                'collaborative_signal': 0.2,  # Weight for similar users' preferences
                'temporal_relevance': 0.1   # Weight for temporal aspects
            }
            
        except Exception as e:
            logger.error(f"Error initializing preference weights: {str(e)}")
            raise
    
    def update_profile(self, user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile with new information."""
        try:
            if user_id not in self.profiles:
                raise ValueError(f"Profile not found for user {user_id}")
            
            profile = self.profiles[user_id]
            
            # Update specific fields
            for field, value in updates.items():
                if field == 'preferences':
                    profile['preferences'].update(self._process_initial_preferences(value))
                elif field in profile:
                    profile[field] = value
            
            profile['last_updated'] = datetime.now()
            
            # Adjust preference weights based on update type
            self._adjust_preference_weights(user_id, updates)
            
            logger.info(f"Updated profile for user {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            raise
    
    def record_interaction(self, user_id: int, interaction: Dict[str, Any]) -> None:
        """Record user interaction with a book."""
        try:
            if user_id not in self.interaction_history:
                self.interaction_history[user_id] = []
            
            interaction['timestamp'] = datetime.now()
            self.interaction_history[user_id].append(interaction)
            
            # Update profile based on interaction
            self._update_profile_from_interaction(user_id, interaction)
            
            # Adjust preference weights
            self._adjust_weights_from_interaction(user_id, interaction)
            
            logger.info(f"Recorded interaction for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error recording interaction: {str(e)}")
            raise
    
    def _update_profile_from_interaction(self, user_id: int, interaction: Dict[str, Any]) -> None:
        """Update user profile based on interaction data."""
        try:
            profile = self.profiles[user_id]
            
            # Update reading history
            if interaction['type'] == 'read':
                profile['reading_history'].append({
                    'book_id': interaction['book_id'],
                    'timestamp': interaction['timestamp'],
                    'rating': interaction.get('rating'),
                    'completion_rate': interaction.get('completion_rate')
                })
            
            # Update genre preferences
            if 'genres' in interaction:
                self._update_genre_preferences(profile, interaction['genres'], interaction.get('rating', 3))
            
            # Update author preferences
            if 'author' in interaction:
                self._update_author_preferences(profile, interaction['author'], interaction.get('rating', 3))
            
        except Exception as e:
            logger.error(f"Error updating profile from interaction: {str(e)}")
            raise
    
    def _update_genre_preferences(self, profile: Dict[str, Any], genres: List[str], rating: float) -> None:
        """Update genre preferences based on interaction."""
        try:
            preferences = profile['preferences']['genre_preferences']
            
            # Calculate rating factor (1-5 scale to -0.2 to +0.2 adjustment)
            adjustment = (rating - 3) * 0.1
            
            for genre in genres:
                if genre in preferences:
                    preferences[genre] = min(1.0, max(0.0, preferences[genre] + adjustment))
                else:
                    preferences[genre] = 0.5 + adjustment
            
            # Renormalize preferences
            profile['preferences']['genre_preferences'] = self._normalize_preferences(preferences)
            
        except Exception as e:
            logger.error(f"Error updating genre preferences: {str(e)}")
            raise
    
    def _update_author_preferences(self, profile: Dict[str, Any], author: str, rating: float) -> None:
        """Update author preferences based on interaction."""
        try:
            favorite_authors = set(profile['favorite_authors'])
            
            # Add to favorites if highly rated
            if rating >= 4:
                favorite_authors.add(author)
            # Remove from favorites if poorly rated
            elif rating <= 2 and author in favorite_authors:
                favorite_authors.remove(author)
            
            profile['favorite_authors'] = list(favorite_authors)
            
        except Exception as e:
            logger.error(f"Error updating author preferences: {str(e)}")
            raise
    
    def _adjust_preference_weights(self, user_id: int, updates: Dict[str, Any]) -> None:
        """Adjust preference weights based on profile updates."""
        try:
            weights = self.preference_weights[user_id]
            
            # Increase weight of explicit preferences if user provides detailed updates
            if 'preferences' in updates:
                weights['explicit_preferences'] = min(0.6, weights['explicit_preferences'] + 0.1)
                weights['implicit_feedback'] = max(0.2, weights['implicit_feedback'] - 0.1)
            
            # Normalize weights
            total = sum(weights.values())
            self.preference_weights[user_id] = {k: v/total for k, v in weights.items()}
            
        except Exception as e:
            logger.error(f"Error adjusting preference weights: {str(e)}")
            raise
    
    def _adjust_weights_from_interaction(self, user_id: int, interaction: Dict[str, Any]) -> None:
        """Adjust preference weights based on user interaction."""
        try:
            weights = self.preference_weights[user_id]
            
            # Increase implicit feedback weight for active users
            if len(self.interaction_history[user_id]) > 10:
                weights['implicit_feedback'] = min(0.4, weights['implicit_feedback'] + 0.05)
                weights['explicit_preferences'] = max(0.3, weights['explicit_preferences'] - 0.05)
            
            # Normalize weights
            total = sum(weights.values())
            self.preference_weights[user_id] = {k: v/total for k, v in weights.items()}
            
        except Exception as e:
            logger.error(f"Error adjusting weights from interaction: {str(e)}")
            raise
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get current user preferences with weights applied."""
        try:
            if user_id not in self.profiles:
                raise ValueError(f"Profile not found for user {user_id}")
            
            profile = self.profiles[user_id]
            weights = self.preference_weights[user_id]
            
            # Combine explicit and implicit preferences
            combined_preferences = {
                'genres': self._combine_preference_sources(profile, weights),
                'authors': profile['favorite_authors'],
                'settings': profile['recommendation_settings'],
                'weights': weights
            }
            
            return combined_preferences
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            raise
    
    def _combine_preference_sources(self, profile: Dict[str, Any], weights: Dict[str, float]) -> Dict[str, float]:
        """Combine different preference sources with weights."""
        try:
            explicit_prefs = profile['preferences']['genre_preferences']
            implicit_prefs = self._calculate_implicit_preferences(profile['reading_history'])
            
            # Combine preferences with weights
            combined = {}
            for genre in set(explicit_prefs.keys()) | set(implicit_prefs.keys()):
                combined[genre] = (
                    weights['explicit_preferences'] * explicit_prefs.get(genre, 0) +
                    weights['implicit_feedback'] * implicit_prefs.get(genre, 0)
                )
            
            return self._normalize_preferences(combined)
            
        except Exception as e:
            logger.error(f"Error combining preference sources: {str(e)}")
            raise
    
    def _calculate_implicit_preferences(self, reading_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate implicit preferences from reading history."""
        try:
            genre_scores = {}
            if not reading_history:
                return genre_scores
            
            # Calculate recency weights
            now = datetime.now()
            max_age = max([(now - h['timestamp']).days for h in reading_history])
            
            for entry in reading_history:
                age_days = (now - entry['timestamp']).days
                recency_weight = 1 - (age_days / max_age) if max_age > 0 else 1
                rating_weight = entry.get('rating', 3) / 5
                
                # Combine weights
                weight = recency_weight * rating_weight
                
                # Update genre scores
                book_data = self.data_loader.get_book_metadata(entry['book_id'])
                if book_data and 'genres' in book_data:
                    for genre in book_data['genres']:
                        genre_scores[genre] = genre_scores.get(genre, 0) + weight
            
            return self._normalize_preferences(genre_scores)
            
        except Exception as e:
            logger.error(f"Error calculating implicit preferences: {str(e)}")
            raise