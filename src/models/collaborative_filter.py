import numpy as np
import pandas as pd
from typing import List, Tuple, Dict
from sklearn.metrics.pairwise import cosine_similarity

class CollaborativeFilter:
    def __init__(self, n_factors: int = 50, learning_rate: float = 0.01, 
                 regularization: float = 0.02, n_epochs: int = 20):
        self.n_factors = n_factors
        self.learning_rate = learning_rate
        self.regularization = regularization
        self.n_epochs = n_epochs
        self.user_factors = None
        self.item_factors = None
        self.user_biases = None
        self.item_biases = None
        self.global_mean = None
        
    def _init_matrices(self, n_users: int, n_items: int) -> None:
        """Initialize model parameters."""
        self.user_factors = np.random.normal(0, 0.1, (n_users, self.n_factors))
        self.item_factors = np.random.normal(0, 0.1, (n_items, self.n_factors))
        self.user_biases = np.zeros(n_users)
        self.item_biases = np.zeros(n_items)
        
    def fit(self, ratings: pd.DataFrame) -> None:
        """Train the collaborative filtering model."""
        try:
            # Create user and item mappings
            self.user_mapping = {uid: idx for idx, uid in enumerate(ratings['user_id'].unique())}
            self.item_mapping = {iid: idx for idx, iid in enumerate(ratings['book_id'].unique())}
            
            # Convert ratings to matrix format
            users = ratings['user_id'].map(self.user_mapping)
            items = ratings['book_id'].map(self.item_mapping)
            ratings_array = ratings['rating'].values
            
            # Initialize matrices
            self._init_matrices(len(self.user_mapping), len(self.item_mapping))
            
            # Calculate global mean
            self.global_mean = ratings_array.mean()
            
            # Training loop
            for epoch in range(self.n_epochs):
                for user, item, rating in zip(users, items, ratings_array):
                    # Predict rating
                    pred = self.global_mean + \
                           self.user_biases[user] + \
                           self.item_biases[item] + \
                           self.user_factors[user].dot(self.item_factors[item])
                    
                    # Calculate error
                    error = rating - pred
                    
                    # Update biases
                    self.user_biases[user] += self.learning_rate * \
                                             (error - self.regularization * self.user_biases[user])
                    self.item_biases[item] += self.learning_rate * \
                                             (error - self.regularization * self.item_biases[item])
                    
                    # Update factors
                    user_factors_update = error * self.item_factors[item] - \
                                        self.regularization * self.user_factors[user]
                    item_factors_update = error * self.user_factors[user] - \
                                        self.regularization * self.item_factors[item]
                    
                    self.user_factors[user] += self.learning_rate * user_factors_update
                    self.item_factors[item] += self.learning_rate * item_factors_update
                    
        except Exception as e:
            raise Exception(f"Error training collaborative filter: {str(e)}")
    
    def predict(self, user_id: int, book_id: int) -> float:
        """Predict rating for a user-item pair."""
        try:
            if user_id not in self.user_mapping or book_id not in self.item_mapping:
                return self.global_mean
            
            user_idx = self.user_mapping[user_id]
            item_idx = self.item_mapping[book_id]
            
            return self.global_mean + \
                   self.user_biases[user_idx] + \
                   self.item_biases[item_idx] + \
                   self.user_factors[user_idx].dot(self.item_factors[item_idx])
        except Exception as e:
            raise Exception(f"Error predicting rating: {str(e)}")
    
    def get_recommendations(self, user_id: int, n_recommendations: int = 5) -> List[Tuple[int, float]]:
        """Get top N recommendations for a user."""
        try:
            if user_id not in self.user_mapping:
                return []
            
            user_idx = self.user_mapping[user_id]
            
            # Calculate predicted ratings for all items
            user_vector = self.user_factors[user_idx]
            predictions = self.global_mean + \
                         self.user_biases[user_idx] + \
                         self.item_biases + \
                         self.item_factors.dot(user_vector)
            
            # Get top N items
            top_items = np.argsort(predictions)[::-1][:n_recommendations]
            
            # Convert back to original item IDs and include predicted ratings
            reverse_mapping = {idx: iid for iid, idx in self.item_mapping.items()}
            recommendations = [(reverse_mapping[idx], predictions[idx]) for idx in top_items]
            
            return recommendations
        except Exception as e:
            raise Exception(f"Error getting recommendations: {str(e)}")