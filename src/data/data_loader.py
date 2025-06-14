import pandas as pd
from typing import Tuple, Dict, Optional
from pathlib import Path
import sqlite3
import json
from contextlib import contextmanager

class DataLoader:
    def __init__(self, data_source: str, source_type: str = "file"):
        """
        Initialize DataLoader with flexible data source support
        Args:
            data_source: Path to file directory or database connection string
            source_type: "file" or "db" or "api"
        """
        self.source_type = source_type
        if source_type == "file":
            self.data_dir = Path(data_source)
            self.books_path = self.data_dir / 'books.csv'
            self.ratings_path = self.data_dir / 'ratings.csv'
            self.tags_path = self.data_dir / 'tags.csv'
            self.book_tags_path = self.data_dir / 'book_tags.csv'
        elif source_type == "db":
            self.db_connection = data_source
        
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        if self.source_type == "db":
            conn = sqlite3.connect(self.db_connection)
            try:
                yield conn
            finally:
                conn.close()
        else:
            yield None

    def load_datasets(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load all required datasets from various sources."""
        try:
            if self.source_type == "file":
                books = pd.read_csv(self.books_path)
                ratings = pd.read_csv(self.ratings_path)
                tags = pd.read_csv(self.tags_path)
                book_tags = pd.read_csv(self.book_tags_path)
            
            elif self.source_type == "db":
                with self.get_connection() as conn:
                    books = pd.read_sql("SELECT * FROM books", conn)
                    ratings = pd.read_sql("SELECT * FROM ratings", conn)
                    tags = pd.read_sql("SELECT * FROM tags", conn)
                    book_tags = pd.read_sql("SELECT * FROM book_tags", conn)
            
            return books, ratings, tags, book_tags
        except Exception as e:
            raise Exception(f"Error loading datasets: {str(e)}")
    
    def merge_book_metadata(self, books: pd.DataFrame, book_tags: pd.DataFrame, 
                          tags: pd.DataFrame) -> pd.DataFrame:
        """Merge books with their tags."""
        try:
            if self.source_type == "db":
                with self.get_connection() as conn:
                    merged_books = pd.read_sql("""
                        SELECT b.*, bt.*, t.tag_name 
                        FROM books b
                        LEFT JOIN book_tags bt ON b.goodreads_book_id = bt.goodreads_book_id
                        LEFT JOIN tags t ON bt.tag_id = t.tag_id
                    """, conn)
                    return merged_books
            
            # For file-based or other sources
            book_tags = book_tags.merge(tags, on='tag_id', how='left')
            merged_books = books.merge(
                book_tags,
                left_on='goodreads_book_id',
                right_on='goodreads_book_id',
                how='left'
            )
            return merged_books
        except Exception as e:
            raise Exception(f"Error merging book metadata: {str(e)}")
    
    def preprocess_tags(self, books: pd.DataFrame) -> pd.DataFrame:
        """Preprocess book tags for feature extraction."""
        try:
            if self.source_type == "db":
                with self.get_connection() as conn:
                    books['all_tags'] = pd.read_sql("""
                        SELECT GROUP_CONCAT(t.tag_name) as tags
                        FROM books b
                        LEFT JOIN book_tags bt ON b.book_id = bt.book_id
                        LEFT JOIN tags t ON bt.tag_id = t.tag_id
                        GROUP BY b.book_id
                    """, conn)
            else:
                books['all_tags'] = books.groupby('book_id')['tag_name'].transform(
                    lambda x: ' '.join(x.dropna())
                )
            
            books = books.drop_duplicates(subset='book_id')
            books.loc[:, 'all_tags'] = books['all_tags'].fillna('')
            
            return books
        except Exception as e:
            raise Exception(f"Error preprocessing tags: {str(e)}")
    
    def get_user_ratings(self, ratings: Optional[pd.DataFrame] = None, user_id: int = None) -> pd.DataFrame:
        """Get ratings for a specific user."""
        try:
            if self.source_type == "db":
                with self.get_connection() as conn:
                    user_ratings = pd.read_sql(
                        "SELECT * FROM ratings WHERE user_id = ?",
                        conn,
                        params=(user_id,)
                    )
                    return user_ratings
            
            if ratings is None:
                _, ratings, _, _ = self.load_datasets()
            
            user_ratings = ratings[ratings['user_id'] == user_id]
            return user_ratings
        except Exception as e:
            raise Exception(f"Error getting user ratings: {str(e)}")