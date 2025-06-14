from typing import Dict, Tuple
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class FeatureExtractor:
    def __init__(self):
        self.tfidf = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
        self.similarity_matrix = None
        self.book_indices = {}
    
    def fit_transform(self, books: pd.DataFrame) -> Tuple[np.ndarray, Dict[str, int]]:
        """Generate TF-IDF features and similarity matrix."""
        try:
            # Generate TF-IDF matrix
            self.tfidf_matrix = self.tfidf.fit_transform(books['all_tags'])
            
            # Compute similarity matrix
            self.similarity_matrix = cosine_similarity(self.tfidf_matrix)
            
            # Create book title to index mapping
            self.book_indices = {title: idx for idx, title in enumerate(books['title'])}
            
            return self.tfidf_matrix, self.book_indices
        except Exception as e:
            raise Exception(f"Error in feature extraction: {str(e)}")
    
    def get_similar_books(self, book_title: str, books: pd.DataFrame, n_recommendations: int = 5) -> pd.DataFrame:
        """Get similar books based on content similarity."""
        try:
            # Find book index
            if book_title not in self.book_indices:
                return pd.DataFrame()
            
            idx = self.book_indices[book_title]
            
            # Get similarity scores
            sim_scores = list(enumerate(self.similarity_matrix[idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            
            # Get top N similar books (excluding the input book)
            sim_scores = sim_scores[1:n_recommendations + 1]
            book_indices = [i[0] for i in sim_scores]
            
            # Return recommended books with similarity scores
            recommendations = books.iloc[book_indices][['title', 'authors', 'average_rating']].copy()
            recommendations['similarity_score'] = [score for _, score in sim_scores]
            
            return recommendations
        except Exception as e:
            raise Exception(f"Error getting similar books: {str(e)}")
    
    def get_feature_importance(self, book_title: str) -> Dict[str, float]:
        """Get important features (tags) for a book."""
        try:
            if book_title not in self.book_indices:
                return {}
            
            idx = self.book_indices[book_title]
            feature_importance = dict(zip(
                self.tfidf.get_feature_names_out(),
                self.tfidf_matrix[idx].toarray()[0]
            ))
            
            # Sort by importance
            return dict(sorted(
                feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            ))
        except Exception as e:
            raise Exception(f"Error getting feature importance: {str(e)}")