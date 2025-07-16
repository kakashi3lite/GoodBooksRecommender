from typing import Dict, Tuple, Optional, List, Any
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.core.logging import StructuredLogger
from src.core.exceptions import GoodBooksException

logger = StructuredLogger(__name__)

class FeatureExtractionError(GoodBooksException):
    """Raised when feature extraction fails"""
    pass

class FeatureExtractor:
    def __init__(self, max_features: Optional[int] = None, ngram_range: Tuple[int, int] = (1, 2)):
        """
        Initialize TF-IDF feature extractor with configurable parameters.
        
        Args:
            max_features: Maximum number of features to extract
            ngram_range: Range of n-grams to consider
        """
        self.tfidf = TfidfVectorizer(
            stop_words='english',
            max_features=max_features,
            ngram_range=ngram_range,
            lowercase=True,
            strip_accents='unicode'
        )
        self.tfidf_matrix: Optional[np.ndarray] = None
        self.similarity_matrix: Optional[np.ndarray] = None
        self.book_indices: Dict[str, int] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    async def fit_transform_async(self, books: pd.DataFrame) -> Tuple[np.ndarray, Dict[str, int]]:
        """
        Generate TF-IDF features and similarity matrix asynchronously.
        
        Args:
            books: DataFrame containing book data with 'all_tags' column
            
        Returns:
            Tuple of TF-IDF matrix and book indices mapping
            
        Raises:
            FeatureExtractionError: If feature extraction fails
        """
        try:
            logger.info("Starting async TF-IDF feature extraction", num_books=len(books))
            
            # Validate input
            if 'all_tags' not in books.columns:
                raise FeatureExtractionError("Books DataFrame must contain 'all_tags' column")
            
            if books.empty:
                raise FeatureExtractionError("Books DataFrame cannot be empty")
            
            # Check for empty or invalid tag data
            tags_series = books['all_tags'].fillna('')
            if tags_series.str.strip().eq('').all():
                # Handle case where all tags are empty by creating empty matrix
                logger.warning("All tag data is empty, creating empty feature matrix")
                self.tfidf_matrix = csr_matrix((len(books), 0))
                self.book_indices = {title: idx for idx, title in enumerate(books['title'])}
                
                # Create empty similarity matrix
                self.similarity_matrix = np.zeros((len(books), len(books)))
                
                logger.info(
                    "TF-IDF feature extraction completed (empty matrix)",
                    matrix_shape=self.tfidf_matrix.shape,
                    num_features=0,
                    num_books=len(self.book_indices)
                )
                return self.tfidf_matrix, self.book_indices
            
            # Run TF-IDF computation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            try:
                self.tfidf_matrix = await loop.run_in_executor(
                    self._executor, 
                    self.tfidf.fit_transform, 
                    tags_series
                )
            except ValueError as ve:
                if "empty vocabulary" in str(ve):
                    # Create a zero matrix for empty vocabulary case
                    logger.warning("Empty vocabulary detected, creating zero feature matrix")
                    self.tfidf_matrix = csr_matrix((len(books), 0))
                else:
                    raise
            
            # Compute similarity matrix asynchronously
            self.similarity_matrix = await loop.run_in_executor(
                self._executor,
                cosine_similarity,
                self.tfidf_matrix
            )
            
            # Create book title to index mapping
            self.book_indices = {title: idx for idx, title in enumerate(books['title'])}
            
            logger.info(
                "TF-IDF feature extraction completed",
                matrix_shape=self.tfidf_matrix.shape,
                num_features=self.tfidf_matrix.shape[1],
                num_books=len(self.book_indices)
            )
            
            return self.tfidf_matrix, self.book_indices
            
        except Exception as e:
            logger.error("Feature extraction failed", error=str(e), exc_info=True)
            raise FeatureExtractionError(f"Error in feature extraction: {str(e)}") from e
    
    def fit_transform(self, books: pd.DataFrame) -> Tuple[np.ndarray, Dict[str, int]]:
        """
        Synchronous wrapper for fit_transform_async.
        
        Args:
            books: DataFrame containing book data with 'all_tags' column
            
        Returns:
            Tuple of TF-IDF matrix and book indices mapping
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.fit_transform_async(books))
            finally:
                loop.close()
        except Exception as e:
            logger.error("Synchronous feature extraction failed", error=str(e))
            raise FeatureExtractionError(f"Error in synchronous feature extraction: {str(e)}") from e

    async def get_similar_books_async(
        self, 
        book_title: str, 
        books: pd.DataFrame, 
        n_recommendations: int = 5
    ) -> pd.DataFrame:
        """
        Get similar books based on content similarity asynchronously.
        
        Args:
            book_title: Title of the book to find similarities for
            books: DataFrame containing book data
            n_recommendations: Number of recommendations to return
            
        Returns:
            DataFrame with recommended books and similarity scores
            
        Raises:
            FeatureExtractionError: If similarity computation fails
        """
        try:
            # Validate that features have been fitted
            if self.similarity_matrix is None or not self.book_indices:
                raise FeatureExtractionError("Features must be fitted before getting similarities")
            
            # Find book index
            if book_title not in self.book_indices:
                logger.warning("Book not found in index", book_title=book_title)
                return pd.DataFrame()
            
            idx = self.book_indices[book_title]
            
            # Get similarity scores asynchronously
            loop = asyncio.get_event_loop()
            sim_scores = await loop.run_in_executor(
                self._executor,
                self._compute_similarity_scores,
                idx
            )
            
            # Get top N similar books (excluding the input book)
            sim_scores = sim_scores[1:n_recommendations + 1]
            book_indices = [i[0] for i in sim_scores]
            
            # Return recommended books with similarity scores
            recommendations = books.iloc[book_indices][['title', 'authors', 'average_rating']].copy()
            recommendations['similarity_score'] = [score for _, score in sim_scores]
            
            logger.info(
                "Similar books computed",
                book_title=book_title,
                num_recommendations=len(recommendations)
            )
            
            return recommendations
            
        except FeatureExtractionError:
            raise
        except Exception as e:
            logger.error("Error getting similar books", book_title=book_title, error=str(e))
            raise FeatureExtractionError(f"Error getting similar books: {str(e)}") from e
    
    def _compute_similarity_scores(self, idx: int) -> List[Tuple[int, float]]:
        """Helper method to compute similarity scores for a book index."""
        sim_scores = list(enumerate(self.similarity_matrix[idx]))
        return sorted(sim_scores, key=lambda x: x[1], reverse=True)
    
    async def get_feature_importance_async(self, book_title: str) -> Dict[str, float]:
        """
        Get important features (tags) for a book asynchronously.
        
        Args:
            book_title: Title of the book to analyze
            
        Returns:
            Dictionary mapping feature names to importance scores
            
        Raises:
            FeatureExtractionError: If feature importance computation fails
        """
        try:
            if self.tfidf_matrix is None:
                raise FeatureExtractionError("Features must be fitted before getting importance")
            
            if book_title not in self.book_indices:
                logger.warning("Book not found for feature importance", book_title=book_title)
                return {}
            
            idx = self.book_indices[book_title]
            
            # Compute feature importance asynchronously
            loop = asyncio.get_event_loop()
            feature_importance = await loop.run_in_executor(
                self._executor,
                self._compute_feature_importance,
                idx
            )
            
            logger.info(
                "Feature importance computed",
                book_title=book_title,
                num_features=len(feature_importance)
            )
            
            return feature_importance
            
        except FeatureExtractionError:
            raise
        except Exception as e:
            logger.error("Error getting feature importance", book_title=book_title, error=str(e))
            raise FeatureExtractionError(f"Error getting feature importance: {str(e)}") from e
    
    def _compute_feature_importance(self, idx: int) -> Dict[str, float]:
        """Helper method to compute feature importance for a book index."""
        feature_importance = dict(zip(
            self.tfidf.get_feature_names_out(),
            self.tfidf_matrix[idx].toarray()[0]
        ))
        
        # Sort by importance and filter out zero values
        return dict(sorted(
            {k: v for k, v in feature_importance.items() if v > 0}.items(),
            key=lambda x: x[1],
            reverse=True
        ))
    
    def get_vocabulary_size(self) -> int:
        """Get the size of the fitted vocabulary."""
        if self.tfidf_matrix is None:
            return 0
        return self.tfidf_matrix.shape[1]
    
    def get_feature_names(self) -> List[str]:
        """Get the feature names from the fitted TF-IDF vectorizer."""
        try:
            if hasattr(self.tfidf, 'get_feature_names_out'):
                return self.tfidf.get_feature_names_out().tolist()
            return []
        except Exception:
            # Handle case when vectorizer is not fitted
            return []
    
    def __del__(self):
        """Cleanup thread pool executor."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)