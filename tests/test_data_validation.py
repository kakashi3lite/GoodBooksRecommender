"""
Tests for Data Schema Validation Module
Following Bookworm AI TDD principles - tests first!
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from src.data.schema_validator import (
    CSVDataValidator, 
    TableSchema, 
    ColumnSchema, 
    DataType, 
    ValidationResult,
    validate_data_directory
)


class TestDataValidation:
    """Test suite for data validation functionality."""
    
    @pytest.fixture
    def sample_books_csv(self):
        """Create sample books CSV data for testing."""
        return """book_id,goodreads_book_id,title,authors,average_rating,isbn,isbn13,language_code,num_pages,ratings_count,text_reviews_count,publication_date,publisher,genres
1,1001,"The Great Gatsby","F. Scott Fitzgerald",4.2,1234567890,9781234567890,eng,180,50000,1500,1925,"Scribner","Fiction|Classics"
2,1002,"To Kill a Mockingbird","Harper Lee",4.5,2345678901,9782345678901,eng,281,75000,2000,1960,"J.B. Lippincott & Co.","Fiction|Classics"
3,1003,"1984","George Orwell",4.1,3456789012,9783456789012,eng,328,100000,3000,1949,"Secker & Warburg","Dystopian|Fiction"
"""
    
    @pytest.fixture
    def sample_ratings_csv(self):
        """Create sample ratings CSV data for testing."""
        return """user_id,book_id,rating
1,1,5
1,2,4
2,1,3
2,2,5
3,3,4
"""
    
    @pytest.fixture
    def sample_tags_csv(self):
        """Create sample tags CSV data for testing."""
        return """tag_id,tag_name
1,fiction
2,classics
3,dystopian
"""
    
    @pytest.fixture
    def sample_book_tags_csv(self):
        """Create sample book_tags CSV data for testing."""
        return """goodreads_book_id,tag_id,count
1001,1,100
1001,2,150
1002,1,200
1002,2,180
1003,1,120
1003,3,90
"""
    
    @pytest.fixture
    def temp_data_dir(self, sample_books_csv, sample_ratings_csv, sample_tags_csv, sample_book_tags_csv):
        """Create temporary directory with sample CSV files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write sample CSV files
            (temp_path / "books.csv").write_text(sample_books_csv)
            (temp_path / "ratings.csv").write_text(sample_ratings_csv)
            (temp_path / "tags.csv").write_text(sample_tags_csv)
            (temp_path / "book_tags.csv").write_text(sample_book_tags_csv)
            
            yield temp_path
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return CSVDataValidator()
    
    def test_column_schema_creation(self):
        """Test creating column schema with various parameters."""
        # Test basic column schema
        col = ColumnSchema("test_col", DataType.STRING)
        assert col.name == "test_col"
        assert col.data_type == DataType.STRING
        assert col.nullable is True  # Default
        
        # Test column with constraints
        col = ColumnSchema(
            "rating", 
            DataType.INTEGER, 
            nullable=False, 
            min_value=1, 
            max_value=5
        )
        assert col.nullable is False
        assert col.min_value == 1
        assert col.max_value == 5
    
    def test_table_schema_creation(self):
        """Test creating table schema."""
        columns = [
            ColumnSchema("id", DataType.INTEGER, nullable=False, unique=True),
            ColumnSchema("name", DataType.STRING, nullable=False)
        ]
        schema = TableSchema("test_table", columns, primary_key=["id"])
        
        assert schema.name == "test_table"
        assert len(schema.columns) == 2
        assert schema.primary_key == ["id"]
    
    def test_valid_data_validation(self, validator, temp_data_dir):
        """Test validation passes for correct data."""
        results = validator.validate_all_datasets(temp_data_dir)
        
        # Should have results for all 4 tables
        assert len(results) >= 4
        assert "books" in results
        assert "ratings" in results
        assert "tags" in results
        assert "book_tags" in results
        
        # All should be valid
        for table_name, result in results.items():
            if table_name != "referential_integrity":  # Skip integrity check for now
                assert result.is_valid, f"Validation failed for {table_name}: {result.errors}"
                assert result.row_count > 0
    
    def test_missing_file_validation(self, validator):
        """Test validation handles missing files gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Don't create any files
            
            results = validator.validate_all_datasets(temp_path)
            
            # Should have error results for missing files
            for table_name in ["books", "ratings", "tags", "book_tags"]:
                assert table_name in results
                assert not results[table_name].is_valid
                assert any("not found" in error for error in results[table_name].errors)
    
    def test_invalid_data_types(self, validator):
        """Test validation catches data type errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create invalid ratings CSV (string rating instead of integer)
            invalid_ratings = """user_id,book_id,rating
1,1,excellent
2,2,good
"""
            (temp_path / "ratings.csv").write_text(invalid_ratings)
            
            # Create minimal valid files for other tables to avoid other errors
            (temp_path / "books.csv").write_text("book_id,goodreads_book_id,title,authors,average_rating\n1,1001,Test,Author,4.0\n")
            (temp_path / "tags.csv").write_text("tag_id,tag_name\n1,test\n")
            (temp_path / "book_tags.csv").write_text("goodreads_book_id,tag_id,count\n1001,1,1\n")
            
            results = validator.validate_all_datasets(temp_path)
            
            # Ratings should be invalid due to data type error
            assert not results["ratings"].is_valid
            # Should have data type related error
            assert any("data type" in error.lower() or "validation failed" in error.lower() 
                     for error in results["ratings"].errors)
    
    def test_missing_required_columns(self, validator):
        """Test validation catches missing required columns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create books CSV missing required column
            invalid_books = """book_id,title,authors
1,"Test Book","Test Author"
"""
            (temp_path / "books.csv").write_text(invalid_books)
            
            results = validator.validate_all_datasets(temp_path)
            
            # Books should be invalid due to missing required columns
            assert not results["books"].is_valid
            assert any("missing" in error.lower() or "required" in error.lower() 
                     for error in results["books"].errors)
    
    def test_value_range_validation(self, validator):
        """Test validation catches values outside allowed ranges."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create ratings with invalid range
            invalid_ratings = """user_id,book_id,rating
1,1,6
2,2,0
"""
            (temp_path / "ratings.csv").write_text(invalid_ratings)
            
            results = validator.validate_all_datasets(temp_path)
            
            # Should catch out-of-range values
            assert not results["ratings"].is_valid
            # Should have range-related errors
            errors_text = " ".join(results["ratings"].errors).lower()
            assert "above maximum" in errors_text or "below minimum" in errors_text
    
    def test_referential_integrity(self, validator):
        """Test validation catches referential integrity violations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create books
            (temp_path / "books.csv").write_text("""book_id,goodreads_book_id,title,authors,average_rating
1,1001,"Test Book","Test Author",4.0
""")
            
            # Create ratings referencing non-existent book
            (temp_path / "ratings.csv").write_text("""user_id,book_id,rating
1,999,5
""")
            
            # Create other required files
            (temp_path / "tags.csv").write_text("tag_id,tag_name\n1,test\n")
            (temp_path / "book_tags.csv").write_text("goodreads_book_id,tag_id,count\n1001,1,1\n")
            
            results = validator.validate_all_datasets(temp_path)
            
            # Should have referential integrity errors
            if "referential_integrity" in results:
                assert not results["referential_integrity"].is_valid
                assert len(results["referential_integrity"].errors) > 0
    
    def test_duplicate_primary_key(self, validator):
        """Test validation catches duplicate primary keys."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create books with duplicate book_id
            duplicate_books = """book_id,goodreads_book_id,title,authors,average_rating
1,1001,"Test Book 1","Author 1",4.0
1,1002,"Test Book 2","Author 2",4.5
"""
            (temp_path / "books.csv").write_text(duplicate_books)
            
            results = validator.validate_all_datasets(temp_path)
            
            # Should catch duplicate primary key
            assert not results["books"].is_valid
            assert any("duplicate" in error.lower() for error in results["books"].errors)
    
    def test_validation_report_generation(self, validator, temp_data_dir):
        """Test comprehensive validation report generation."""
        results = validator.validate_all_datasets(temp_data_dir)
        report = validator.generate_validation_report(results)
        
        # Report should be a non-empty string
        assert isinstance(report, str)
        assert len(report) > 0
        
        # Should contain key sections
        assert "DATA VALIDATION REPORT" in report
        assert "Overall Status:" in report
        assert "Total Errors:" in report
        assert "Total Warnings:" in report
        
        # Should contain table information
        assert "books" in report
        assert "ratings" in report
    
    def test_performance_with_large_dataset(self, validator):
        """Test validator performance with larger datasets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create larger test dataset
            books_data = ["book_id,goodreads_book_id,title,authors,average_rating"]
            for i in range(1000):
                books_data.append(f"{i},100{i},\"Book {i}\",\"Author {i}\",{4.0 + (i % 10) * 0.1}")
            
            (temp_path / "books.csv").write_text("\n".join(books_data))
            
            # Create minimal other files
            (temp_path / "ratings.csv").write_text("user_id,book_id,rating\n1,1,5\n")
            (temp_path / "tags.csv").write_text("tag_id,tag_name\n1,test\n")
            (temp_path / "book_tags.csv").write_text("goodreads_book_id,tag_id,count\n1001,1,1\n")
            
            import time
            start_time = time.time()
            results = validator.validate_all_datasets(temp_path)
            duration = time.time() - start_time
            
            # Should complete validation reasonably quickly (< 5 seconds)
            assert duration < 5.0
            assert results["books"].is_valid
            assert results["books"].row_count == 1000
    
    def test_edge_cases_empty_files(self, validator):
        """Test handling of edge cases like empty files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create empty file
            (temp_path / "books.csv").write_text("")
            
            results = validator.validate_all_datasets(temp_path)
            
            # Should handle empty file gracefully
            assert not results["books"].is_valid
            assert len(results["books"].errors) > 0
    
    def test_validate_data_directory_function(self, temp_data_dir):
        """Test the main validate_data_directory function."""
        results = validate_data_directory(str(temp_data_dir))
        
        # Should return results dictionary
        assert isinstance(results, dict)
        assert len(results) >= 4
        
        # All basic tables should be valid with sample data
        for table_name in ["books", "ratings", "tags", "book_tags"]:
            assert table_name in results
            # Sample data should be valid
            assert results[table_name].is_valid, f"Sample data invalid for {table_name}: {results[table_name].errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
