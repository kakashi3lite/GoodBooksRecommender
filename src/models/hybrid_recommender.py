from typing import List, Dict, Tuple
import pandas as pd
import numpy as np
from src.features.feature_extractor import FeatureExtractor
from src.models.collaborative_filter import CollaborativeFilter

class HybridRecommender:
    def __init__(self, content_weight: float = 0.5):
        """Initialize hybrid recommender with content and collaborative components.
        
        Args:
            content_weight: Weight for content-based recommendations (0-1)
        """
        self.content_weight = content_weight
        self.collab_weight = 1 - content_weight
        self.content_recommender = FeatureExtractor()
        self.collab_recommender = CollaborativeFilter()
        self.books_data = None
        
    def fit(self, books: pd.DataFrame, ratings: pd.DataFrame) -> None:
        """Train both recommendation models."""
        try:
            # Store books data for later use
            self.books_data = books
            
            # Train content-based model
            self.content_recommender.fit_transform(books)
            
            # Train collaborative filtering model
            self.collab_recommender.fit(ratings)
            
        except Exception as e:
            raise Exception(f"Error training hybrid recommender: {str(e)}")
    
    def get_recommendations(self, user_id: int = None, book_title: str = None,
                           n_recommendations: int = 5) -> pd.DataFrame:
        """Get hybrid recommendations based on user ID and/or book title.
        
        Args:
            user_id: Optional user ID for collaborative filtering
            book_title: Optional book title for content-based filtering
            n_recommendations: Number of recommendations to return
            
        Returns:
            DataFrame with recommended books and scores
        """
        try:
            content_scores = {}
            collab_scores = {}
            
            # Get content-based recommendations if book title is provided
            if book_title is not None:
                content_recs = self.content_recommender.get_similar_books(
                    book_title,
                    self.books_data,
                    n_recommendations=n_recommendations
                )
                if not content_recs.empty:
                    for _, row in content_recs.iterrows():
                        content_scores[row['title']] = row['similarity_score']
            
            # Get collaborative filtering recommendations if user ID is provided
            if user_id is not None:
                collab_recs = self.collab_recommender.get_recommendations(
                    user_id,
                    n_recommendations=n_recommendations
                )
                for book_id, score in collab_recs:
                    book_title = self.books_data[
                        self.books_data['book_id'] == book_id
                    ]['title'].iloc[0]
                    collab_scores[book_title] = score
            
            # Combine and normalize scores
            all_books = set(content_scores.keys()) | set(collab_scores.keys())
            hybrid_scores = {}
            
            for book in all_books:
                # Normalize individual scores
                content_score = content_scores.get(book, 0)
                collab_score = collab_scores.get(book, 0)
                
                if content_scores and collab_scores:  # Both components available
                    hybrid_scores[book] = (self.content_weight * content_score +
                                         self.collab_weight * collab_score)
                elif content_scores:  # Only content-based available
                    hybrid_scores[book] = content_score
                else:  # Only collaborative available
                    hybrid_scores[book] = collab_score
            
            # Sort and prepare recommendations DataFrame
            sorted_recs = sorted(hybrid_scores.items(),
                                key=lambda x: x[1],
                                reverse=True)[:n_recommendations]
            
            recommendations = pd.DataFrame(
                sorted_recs,
                columns=['title', 'hybrid_score']
            )
            
            # Add book metadata
            recommendations = recommendations.merge(
                self.books_data[['title', 'authors', 'average_rating']],
                on='title',
                how='left'
            )
            
            return recommendations
            
        except Exception as e:
            raise Exception(f"Error getting hybrid recommendations: {str(e)}")
    
    def explain_recommendations(self, book_title: str) -> Dict[str, List[str]]:
        """Provide explanation for content-based recommendations."""
        try:
            explanations = {
                'top_tags': [],
                'similar_books': []
            }
            
            # Get feature importance
            feature_importance = self.content_recommender.get_feature_importance(book_title)
            explanations['top_tags'] = list(feature_importance.keys())[:5]
            
            # Get similar books with high content similarity
            similar_books = self.content_recommender.get_similar_books(
                book_title,
                self.books_data,
                n_recommendations=3
            )
            if not similar_books.empty:
                explanations['similar_books'] = similar_books['title'].tolist()
            
            return explanations
            
        except Exception as e:
            raise Exception(f"Error explaining recommendations: {str(e)}")