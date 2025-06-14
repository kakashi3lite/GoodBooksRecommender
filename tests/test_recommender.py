import pytest
import pandas as pd
import numpy as np
from src.data.data_loader import DataLoader
from src.features.feature_extractor import FeatureExtractor
from src.models.collaborative_filter import CollaborativeFilter
from src.models.hybrid_recommender import HybridRecommender

@pytest.fixture
def sample_books_data():
    return pd.DataFrame({
        'book_id': [1, 2, 3],
        'goodreads_book_id': [1001, 1002, 1003],
        'title': ['Book 1', 'Book 2', 'Book 3'],
        'authors': ['Author 1', 'Author 2', 'Author 3'],
        'average_rating': [4.5, 4.0, 3.5],
        'tag_name': ['fiction fantasy', 'fiction mystery', 'non-fiction']
    })

@pytest.fixture
def sample_ratings_data():
    return pd.DataFrame({
        'user_id': [1, 1, 2, 2, 3],
        'book_id': [1, 2, 2, 3, 1],
        'rating': [5, 4, 3, 5, 4]
    })

def test_feature_extractor(sample_books_data):
    extractor = FeatureExtractor()
    
    # Test fit_transform
    tfidf_matrix, book_indices = extractor.fit_transform(sample_books_data)
    assert tfidf_matrix.shape[0] == len(sample_books_data)
    assert len(book_indices) == len(sample_books_data)
    
    # Test get_similar_books
    recommendations = extractor.get_similar_books('Book 1', sample_books_data)
    assert not recommendations.empty
    assert 'title' in recommendations.columns
    assert len(recommendations) <= 5  # Default n_recommendations

def test_collaborative_filter(sample_ratings_data):
    cf = CollaborativeFilter(n_factors=2, n_epochs=2)
    
    # Test fit
    cf.fit(sample_ratings_data)
    assert cf.user_factors is not None
    assert cf.item_factors is not None
    
    # Test predict
    prediction = cf.predict(user_id=1, book_id=1)
    assert isinstance(prediction, float)
    assert 0 <= prediction <= 5  # Rating scale
    
    # Test get_recommendations
    recommendations = cf.get_recommendations(user_id=1)
    assert len(recommendations) > 0
    assert all(isinstance(rec, tuple) for rec in recommendations)

def test_hybrid_recommender(sample_books_data, sample_ratings_data):
    recommender = HybridRecommender(content_weight=0.5)
    
    # Test fit
    recommender.fit(sample_books_data, sample_ratings_data)
    
    # Test get_recommendations with only user_id
    user_recs = recommender.get_recommendations(user_id=1)
    assert not user_recs.empty
    assert 'hybrid_score' in user_recs.columns
    
    # Test get_recommendations with only book_title
    book_recs = recommender.get_recommendations(book_title='Book 1')
    assert not book_recs.empty
    assert 'hybrid_score' in book_recs.columns
    
    # Test get_recommendations with both
    hybrid_recs = recommender.get_recommendations(user_id=1, book_title='Book 1')
    assert not hybrid_recs.empty
    assert 'hybrid_score' in hybrid_recs.columns

def test_explanation_feature(sample_books_data, sample_ratings_data):
    recommender = HybridRecommender()
    recommender.fit(sample_books_data, sample_ratings_data)
    
    explanation = recommender.explain_recommendations('Book 1')
    assert isinstance(explanation, dict)
    assert 'top_tags' in explanation
    assert 'similar_books' in explanation
    assert len(explanation['top_tags']) <= 5

def test_edge_cases(sample_books_data, sample_ratings_data):
    recommender = HybridRecommender()
    recommender.fit(sample_books_data, sample_ratings_data)
    
    # Test with non-existent user
    recs = recommender.get_recommendations(user_id=999)
    assert not recs.empty  # Should fall back to content-based
    
    # Test with non-existent book
    recs = recommender.get_recommendations(book_title='Non-existent Book')
    assert recs.empty  # Should return empty DataFrame
    
    # Test with invalid content_weight
    with pytest.raises(Exception):
        HybridRecommender(content_weight=1.5)