"""
Comprehensive unit tests for TF-IDF edge cases and feature extraction.
Tests designed to achieve ≥90% coverage with rigorous edge case validation.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from sklearn.feature_extraction.text import TfidfVectorizer

from src.features.feature_extractor import FeatureExtractor, FeatureExtractionError
from src.data.data_loader import DataLoader, DataLoadError


class TestFeatureExtractorEdgeCases:
    """Test suite for FeatureExtractor edge cases and error conditions."""
    
    @pytest.fixture
    def sample_books_data(self):
        """Sample books data for testing."""
        return pd.DataFrame({
            'title': ['Book A', 'Book B', 'Book C', 'Book D'],
            'authors': ['Author 1', 'Author 2', 'Author 3', 'Author 4'],
            'average_rating': [4.5, 3.8, 4.2, 3.9],
            'all_tags': [
                'fiction fantasy adventure',
                'mystery thriller crime',
                'romance drama love',
                'science fiction space'
            ]
        })
    
    @pytest.fixture
    def empty_books_data(self):
        """Empty books DataFrame for testing."""
        return pd.DataFrame(columns=['title', 'authors', 'average_rating', 'all_tags'])
    
    @pytest.fixture
    def malformed_books_data(self):
        """Malformed books data missing required columns."""
        return pd.DataFrame({
            'title': ['Book A', 'Book B'],
            'authors': ['Author 1', 'Author 2']
            # Missing 'all_tags' column
        })
    
    def test_feature_extractor_initialization_default(self):
        """Test FeatureExtractor initialization with default parameters."""
        extractor = FeatureExtractor()
        assert extractor.tfidf_matrix is None
        assert extractor.similarity_matrix is None
        assert extractor.book_indices == {}
        assert extractor.tfidf.stop_words == 'english'
        assert extractor.tfidf.ngram_range == (1, 2)
    
    def test_feature_extractor_initialization_custom(self):
        """Test FeatureExtractor initialization with custom parameters."""
        extractor = FeatureExtractor(max_features=1000, ngram_range=(1, 3))
        assert extractor.tfidf.max_features == 1000
        assert extractor.tfidf.ngram_range == (1, 3)
    
    @pytest.mark.asyncio
    async def test_fit_transform_async_success(self, sample_books_data):
        """Test successful async fit_transform operation."""
        extractor = FeatureExtractor()
        
        tfidf_matrix, book_indices = await extractor.fit_transform_async(sample_books_data)
        
        assert tfidf_matrix is not None
        assert tfidf_matrix.shape[0] == len(sample_books_data)
        assert len(book_indices) == len(sample_books_data)
        assert extractor.similarity_matrix is not None
        assert extractor.similarity_matrix.shape == (len(sample_books_data), len(sample_books_data))
        
        # Verify book indices mapping
        for idx, title in enumerate(sample_books_data['title']):
            assert book_indices[title] == idx
    
    @pytest.mark.asyncio
    async def test_fit_transform_async_empty_dataframe(self, empty_books_data):
        """Test fit_transform with empty DataFrame."""
        extractor = FeatureExtractor()
        
        with pytest.raises(FeatureExtractionError, match="Books DataFrame cannot be empty"):
            await extractor.fit_transform_async(empty_books_data)
    
    @pytest.mark.asyncio
    async def test_fit_transform_async_missing_column(self, malformed_books_data):
        """Test fit_transform with missing 'all_tags' column."""
        extractor = FeatureExtractor()
        
        with pytest.raises(FeatureExtractionError, match="Books DataFrame must contain 'all_tags' column"):
            await extractor.fit_transform_async(malformed_books_data)
    
    @pytest.mark.asyncio
    async def test_fit_transform_async_nan_values(self):
        """Test fit_transform with NaN values in all_tags column."""
        books_with_nan = pd.DataFrame({
            'title': ['Book A', 'Book B', 'Book C'],
            'authors': ['Author 1', 'Author 2', 'Author 3'],
            'average_rating': [4.5, 3.8, 4.2],
            'all_tags': ['fiction fantasy', np.nan, 'romance']
        })
        
        extractor = FeatureExtractor()
        tfidf_matrix, book_indices = await extractor.fit_transform_async(books_with_nan)
        
        # Should handle NaN values by filling with empty string
        assert tfidf_matrix is not None
        assert len(book_indices) == 3
    
    @pytest.mark.asyncio
    async def test_fit_transform_async_empty_tags(self):
        """Test fit_transform with empty tag strings."""
        books_empty_tags = pd.DataFrame({
            'title': ['Book A', 'Book B', 'Book C'],
            'authors': ['Author 1', 'Author 2', 'Author 3'],
            'average_rating': [4.5, 3.8, 4.2],
            'all_tags': ['', '', '']
        })
        
        extractor = FeatureExtractor()
        tfidf_matrix, book_indices = await extractor.fit_transform_async(books_empty_tags)
        
        # Should handle empty tags gracefully
        assert tfidf_matrix is not None
        assert tfidf_matrix.shape[1] == 0  # No features extracted from empty strings
    
    @pytest.mark.asyncio
    async def test_fit_transform_async_single_book(self):
        """Test fit_transform with single book."""
        single_book = pd.DataFrame({
            'title': ['Book A'],
            'authors': ['Author 1'],
            'average_rating': [4.5],
            'all_tags': ['fiction fantasy adventure']
        })
        
        extractor = FeatureExtractor()
        tfidf_matrix, book_indices = await extractor.fit_transform_async(single_book)
        
        assert tfidf_matrix.shape[0] == 1
        assert len(book_indices) == 1
        assert 'Book A' in book_indices
    
    @pytest.mark.asyncio
    async def test_fit_transform_async_execution_error(self, sample_books_data):
        """Test fit_transform when TfidfVectorizer raises exception."""
        extractor = FeatureExtractor()
        
        with patch.object(extractor.tfidf, 'fit_transform', side_effect=ValueError("TF-IDF error")):
            with pytest.raises(FeatureExtractionError, match="Error in feature extraction"):
                await extractor.fit_transform_async(sample_books_data)
    
    @pytest.mark.asyncio
    async def test_get_similar_books_async_success(self, sample_books_data):
        """Test successful similar books retrieval."""
        extractor = FeatureExtractor()
        await extractor.fit_transform_async(sample_books_data)
        
        similar_books = await extractor.get_similar_books_async('Book A', sample_books_data, 2)
        
        assert isinstance(similar_books, pd.DataFrame)
        assert len(similar_books) <= 2
        assert 'similarity_score' in similar_books.columns
        assert 'title' in similar_books.columns
        assert 'authors' in similar_books.columns
        assert 'average_rating' in similar_books.columns
        
        # Verify Book A is not in the recommendations
        assert 'Book A' not in similar_books['title'].values
    
    @pytest.mark.asyncio
    async def test_get_similar_books_async_not_fitted(self, sample_books_data):
        """Test similar books retrieval when features haven't been fitted."""
        extractor = FeatureExtractor()
        
        with pytest.raises(FeatureExtractionError, match="Features must be fitted before getting similarities"):
            await extractor.get_similar_books_async('Book A', sample_books_data, 2)
    
    @pytest.mark.asyncio
    async def test_get_similar_books_async_book_not_found(self, sample_books_data):
        """Test similar books retrieval for non-existent book."""
        extractor = FeatureExtractor()
        await extractor.fit_transform_async(sample_books_data)
        
        similar_books = await extractor.get_similar_books_async('Nonexistent Book', sample_books_data, 2)
        
        assert isinstance(similar_books, pd.DataFrame)
        assert len(similar_books) == 0
    
    @pytest.mark.asyncio
    async def test_get_similar_books_async_zero_recommendations(self, sample_books_data):
        """Test similar books retrieval with zero recommendations requested."""
        extractor = FeatureExtractor()
        await extractor.fit_transform_async(sample_books_data)
        
        similar_books = await extractor.get_similar_books_async('Book A', sample_books_data, 0)
        
        assert isinstance(similar_books, pd.DataFrame)
        assert len(similar_books) == 0
    
    @pytest.mark.asyncio
    async def test_get_similar_books_async_more_recs_than_books(self, sample_books_data):
        """Test similar books retrieval requesting more books than available."""
        extractor = FeatureExtractor()
        await extractor.fit_transform_async(sample_books_data)
        
        similar_books = await extractor.get_similar_books_async('Book A', sample_books_data, 10)
        
        # Should return all available books except the queried one
        assert len(similar_books) == len(sample_books_data) - 1
    
    @pytest.mark.asyncio
    async def test_get_feature_importance_async_success(self, sample_books_data):
        """Test successful feature importance retrieval."""
        extractor = FeatureExtractor()
        await extractor.fit_transform_async(sample_books_data)
        
        importance = await extractor.get_feature_importance_async('Book A')
        
        assert isinstance(importance, dict)
        assert len(importance) > 0
        
        # All values should be positive (filtered out zeros)
        for value in importance.values():
            assert value > 0
        
        # Should be sorted in descending order
        values = list(importance.values())
        assert values == sorted(values, reverse=True)
    
    @pytest.mark.asyncio
    async def test_get_feature_importance_async_not_fitted(self):
        """Test feature importance retrieval when features haven't been fitted."""
        extractor = FeatureExtractor()
        
        with pytest.raises(FeatureExtractionError, match="Features must be fitted before getting importance"):
            await extractor.get_feature_importance_async('Book A')
    
    @pytest.mark.asyncio
    async def test_get_feature_importance_async_book_not_found(self, sample_books_data):
        """Test feature importance retrieval for non-existent book."""
        extractor = FeatureExtractor()
        await extractor.fit_transform_async(sample_books_data)
        
        importance = await extractor.get_feature_importance_async('Nonexistent Book')
        
        assert isinstance(importance, dict)
        assert len(importance) == 0
    
    def test_get_vocabulary_size_not_fitted(self):
        """Test vocabulary size when not fitted."""
        extractor = FeatureExtractor()
        assert extractor.get_vocabulary_size() == 0
    
    @pytest.mark.asyncio
    async def test_get_vocabulary_size_fitted(self, sample_books_data):
        """Test vocabulary size when fitted."""
        extractor = FeatureExtractor()
        await extractor.fit_transform_async(sample_books_data)
        
        vocab_size = extractor.get_vocabulary_size()
        assert vocab_size > 0
        assert vocab_size == extractor.tfidf_matrix.shape[1]
    
    def test_get_feature_names_not_fitted(self):
        """Test feature names when not fitted."""
        extractor = FeatureExtractor()
        feature_names = extractor.get_feature_names()
        assert feature_names == []
    
    @pytest.mark.asyncio
    async def test_get_feature_names_fitted(self, sample_books_data):
        """Test feature names when fitted."""
        extractor = FeatureExtractor()
        await extractor.fit_transform_async(sample_books_data)
        
        feature_names = extractor.get_feature_names()
        assert isinstance(feature_names, list)
        assert len(feature_names) > 0
        assert len(feature_names) == extractor.get_vocabulary_size()
    
    def test_destructor(self):
        """Test that destructor properly shuts down thread pool."""
        extractor = FeatureExtractor()
        executor = extractor._executor
        
        # Simulate deletion
        del extractor
        
        # Thread pool should be shutdown
        assert executor._shutdown
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, sample_books_data):
        """Test concurrent feature extraction operations."""
        extractor = FeatureExtractor()
        await extractor.fit_transform_async(sample_books_data)
        
        # Run multiple operations concurrently
        tasks = [
            extractor.get_similar_books_async('Book A', sample_books_data, 2),
            extractor.get_similar_books_async('Book B', sample_books_data, 2),
            extractor.get_feature_importance_async('Book A'),
            extractor.get_feature_importance_async('Book B')
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All operations should complete successfully
        assert len(results) == 4
        assert isinstance(results[0], pd.DataFrame)  # Similar books for A
        assert isinstance(results[1], pd.DataFrame)  # Similar books for B
        assert isinstance(results[2], dict)          # Feature importance for A
        assert isinstance(results[3], dict)          # Feature importance for B


class TestDataLoaderEdgeCases:
    """Test suite for DataLoader edge cases and async operations."""
    
    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create temporary data directory with CSV files."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Create sample CSV files
        books_df = pd.DataFrame({
            'book_id': [1, 2, 3],
            'title': ['Book A', 'Book B', 'Book C'],
            'goodreads_book_id': [101, 102, 103]
        })
        books_df.to_csv(data_dir / 'books.csv', index=False)
        
        ratings_df = pd.DataFrame({
            'user_id': [1, 1, 2],
            'book_id': [1, 2, 1],
            'rating': [5, 4, 3]
        })
        ratings_df.to_csv(data_dir / 'ratings.csv', index=False)
        
        tags_df = pd.DataFrame({
            'tag_id': [1, 2, 3],
            'tag_name': ['fiction', 'fantasy', 'romance']
        })
        tags_df.to_csv(data_dir / 'tags.csv', index=False)
        
        book_tags_df = pd.DataFrame({
            'book_id': [1, 1, 2],
            'tag_id': [1, 2, 3]
        })
        book_tags_df.to_csv(data_dir / 'book_tags.csv', index=False)
        
        return data_dir
    
    def test_data_loader_initialization_file_source(self, temp_data_dir):
        """Test DataLoader initialization with file source."""
        loader = DataLoader(str(temp_data_dir), source_type="file")
        
        assert loader.source_type == "file"
        assert loader.data_dir == temp_data_dir
        assert loader.books_path.exists()
        assert loader.ratings_path.exists()
        assert loader.tags_path.exists()
        assert loader.book_tags_path.exists()
    
    def test_data_loader_initialization_missing_files(self, tmp_path):
        """Test DataLoader initialization with missing files."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        with pytest.raises(DataLoadError, match="Missing required files"):
            DataLoader(str(empty_dir), source_type="file")
    
    def test_data_loader_initialization_db_source(self):
        """Test DataLoader initialization with database source."""
        loader = DataLoader("test.db", source_type="db")
        
        assert loader.source_type == "db"
        assert loader.db_connection == "test.db"
    
    @pytest.mark.asyncio
    async def test_load_datasets_async_file_source(self, temp_data_dir):
        """Test async dataset loading from files."""
        loader = DataLoader(str(temp_data_dir), source_type="file")
        
        books, ratings, tags, book_tags = await loader.load_datasets_async()
        
        assert isinstance(books, pd.DataFrame)
        assert isinstance(ratings, pd.DataFrame)
        assert isinstance(tags, pd.DataFrame)
        assert isinstance(book_tags, pd.DataFrame)
        
        assert len(books) == 3
        assert len(ratings) == 3
        assert len(tags) == 3
        assert len(book_tags) == 3
    
    @pytest.mark.asyncio
    async def test_load_datasets_async_empty_files(self, tmp_path):
        """Test async dataset loading with empty CSV files."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Create empty CSV files with headers only
        for filename in ['books.csv', 'ratings.csv', 'tags.csv', 'book_tags.csv']:
            pd.DataFrame().to_csv(data_dir / filename, index=False)
        
        loader = DataLoader(str(data_dir), source_type="file")
        
        with pytest.raises(DataLoadError, match="No columns to parse from file"):
            await loader.load_datasets_async()
    
    @pytest.mark.asyncio
    async def test_load_datasets_async_malformed_csv(self, tmp_path):
        """Test async dataset loading with malformed CSV files."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Create CSV files with missing required columns
        books_df = pd.DataFrame({'title': ['Book A']})  # Missing book_id
        books_df.to_csv(data_dir / 'books.csv', index=False)
        
        ratings_df = pd.DataFrame({'user_id': [1], 'book_id': [1], 'rating': [5]})
        ratings_df.to_csv(data_dir / 'ratings.csv', index=False)
        
        tags_df = pd.DataFrame({'tag_id': [1], 'tag_name': ['fiction']})
        tags_df.to_csv(data_dir / 'tags.csv', index=False)
        
        book_tags_df = pd.DataFrame({'book_id': [1], 'tag_id': [1]})
        book_tags_df.to_csv(data_dir / 'book_tags.csv', index=False)
        
        loader = DataLoader(str(data_dir), source_type="file")
        
        with pytest.raises(DataLoadError, match="missing required columns"):
            await loader.load_datasets_async()
    
    @pytest.mark.asyncio
    async def test_load_datasets_async_unsupported_source(self):
        """Test async dataset loading with unsupported source type."""
        loader = DataLoader("dummy", source_type="unsupported")
        
        with pytest.raises(DataLoadError, match="Unsupported source type"):
            await loader.load_datasets_async()
    
    @pytest.mark.asyncio
    async def test_get_user_ratings_async_missing_user_id(self, temp_data_dir):
        """Test async user ratings retrieval without user ID."""
        loader = DataLoader(str(temp_data_dir), source_type="file")
        
        with pytest.raises(DataLoadError, match="user_id must be provided"):
            await loader.get_user_ratings_async()
    
    @pytest.mark.asyncio
    async def test_get_user_ratings_async_valid_user(self, temp_data_dir):
        """Test async user ratings retrieval for valid user."""
        loader = DataLoader(str(temp_data_dir), source_type="file")
        
        user_ratings = await loader.get_user_ratings_async(user_id=1)
        
        assert isinstance(user_ratings, pd.DataFrame)
        assert len(user_ratings) == 2  # User 1 has 2 ratings
        assert all(user_ratings['user_id'] == 1)
    
    @pytest.mark.asyncio
    async def test_get_user_ratings_async_nonexistent_user(self, temp_data_dir):
        """Test async user ratings retrieval for non-existent user."""
        loader = DataLoader(str(temp_data_dir), source_type="file")
        
        user_ratings = await loader.get_user_ratings_async(user_id=999)
        
        assert isinstance(user_ratings, pd.DataFrame)
        assert len(user_ratings) == 0
    
    @pytest.mark.asyncio
    async def test_get_book_metadata_async_valid_book(self, temp_data_dir):
        """Test async book metadata retrieval for valid book."""
        loader = DataLoader(str(temp_data_dir), source_type="file")
        
        metadata = await loader.get_book_metadata_async(book_id=1)
        
        assert isinstance(metadata, dict)
        assert metadata['book_id'] == 1
        assert metadata['title'] == 'Book A'
    
    @pytest.mark.asyncio
    async def test_get_book_metadata_async_nonexistent_book(self, temp_data_dir):
        """Test async book metadata retrieval for non-existent book."""
        loader = DataLoader(str(temp_data_dir), source_type="file")
        
        metadata = await loader.get_book_metadata_async(book_id=999)
        
        assert metadata is None
    
    def test_data_loader_destructor(self, temp_data_dir):
        """Test that DataLoader destructor properly shuts down thread pool."""
        loader = DataLoader(str(temp_data_dir), source_type="file")
        executor = loader._executor
        
        # Simulate deletion
        del loader
        
        # Thread pool should be shutdown
        assert executor._shutdown


class TestTFIDFPerformance:
    """Performance tests for TF-IDF operations."""
    
    @pytest.mark.asyncio
    async def test_large_dataset_performance(self):
        """Test TF-IDF performance with large dataset."""
        # Create large dataset
        num_books = 1000
        large_books = pd.DataFrame({
            'title': [f'Book {i}' for i in range(num_books)],
            'authors': [f'Author {i}' for i in range(num_books)],
            'average_rating': np.random.uniform(1, 5, num_books),
            'all_tags': [f'tag{i % 10} tag{(i+1) % 10} tag{(i+2) % 10}' for i in range(num_books)]
        })
        
        extractor = FeatureExtractor(max_features=500)  # Limit features for performance
        
        import time
        start_time = time.time()
        await extractor.fit_transform_async(large_books)
        fit_time = time.time() - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert fit_time < 30.0  # 30 seconds
        
        start_time = time.time()
        similar_books = await extractor.get_similar_books_async('Book 0', large_books, 10)
        query_time = time.time() - start_time
        
        # Query should be fast
        assert query_time < 5.0  # 5 seconds
        assert len(similar_books) == 10
    
    @pytest.mark.asyncio
    async def test_memory_usage_large_dataset(self):
        """Test memory usage with large dataset."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        num_books = 5000
        large_books = pd.DataFrame({
            'title': [f'Book {i}' for i in range(num_books)],
            'authors': [f'Author {i}' for i in range(num_books)],
            'average_rating': np.random.uniform(1, 5, num_books),
            'all_tags': [f'tag{i % 20} tag{(i+1) % 20}' for i in range(num_books)]
        })
        
        extractor = FeatureExtractor(max_features=1000)
        await extractor.fit_transform_async(large_books)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (adjust threshold as needed)
        assert memory_increase < 500  # 500 MB
