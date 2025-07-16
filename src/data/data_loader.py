import pandas as pd
from typing import Tuple, Dict, Optional, Any, Union
from pathlib import Path
import sqlite3
import json
import asyncio
import aiofiles
import aiosqlite
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from src.core.logging import StructuredLogger
from src.core.exceptions import GoodBooksException

logger = StructuredLogger(__name__)

class DataLoadError(GoodBooksException):
    """Raised when data loading fails"""
    pass

class DataLoader:
    def __init__(self, data_source: str, source_type: str = "file"):
        """
        Initialize DataLoader with flexible data source support.
        
        Args:
            data_source: Path to file directory or database connection string
            source_type: "file" or "db" or "api"
        """
        self.source_type = source_type
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        if source_type == "file":
            self.data_dir = Path(data_source)
            self.books_path = self.data_dir / 'books.csv'
            self.ratings_path = self.data_dir / 'ratings.csv'
            self.tags_path = self.data_dir / 'tags.csv'
            self.book_tags_path = self.data_dir / 'book_tags.csv'
            self._validate_file_paths()
        elif source_type == "db":
            self.db_connection = data_source
    
    def _validate_file_paths(self) -> None:
        """Validate that all required CSV files exist."""
        required_files = [self.books_path, self.ratings_path, self.tags_path, self.book_tags_path]
        missing_files = [f for f in required_files if not f.exists()]
        
        if missing_files:
            raise DataLoadError(f"Missing required files: {[str(f) for f in missing_files]}")
    
    @asynccontextmanager
    async def get_async_connection(self):
        """Async context manager for database connections."""
        if self.source_type == "db":
            conn = await aiosqlite.connect(self.db_connection)
            try:
                yield conn
            finally:
                await conn.close()
        else:
            yield None

    async def load_datasets_async(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load all required datasets from various sources asynchronously.
        
        Returns:
            Tuple of (books, ratings, tags, book_tags) DataFrames
            
        Raises:
            DataLoadError: If data loading fails
        """
        try:
            logger.info("Starting async dataset loading", source_type=self.source_type)
            
            if self.source_type == "file":
                # Load CSV files asynchronously using thread pool
                loop = asyncio.get_event_loop()
                books, ratings, tags, book_tags = await asyncio.gather(
                    loop.run_in_executor(self._executor, pd.read_csv, str(self.books_path)),
                    loop.run_in_executor(self._executor, pd.read_csv, str(self.ratings_path)),
                    loop.run_in_executor(self._executor, pd.read_csv, str(self.tags_path)),
                    loop.run_in_executor(self._executor, pd.read_csv, str(self.book_tags_path))
                )
            
            elif self.source_type == "db":
                async with self.get_async_connection() as conn:
                    books_task = self._read_sql_async(conn, "SELECT * FROM books")
                    ratings_task = self._read_sql_async(conn, "SELECT * FROM ratings")
                    tags_task = self._read_sql_async(conn, "SELECT * FROM tags")
                    book_tags_task = self._read_sql_async(conn, "SELECT * FROM book_tags")
                    
                    books, ratings, tags, book_tags = await asyncio.gather(
                        books_task, ratings_task, tags_task, book_tags_task
                    )
            else:
                raise DataLoadError(f"Unsupported source type: {self.source_type}")
            
            # Validate loaded data
            self._validate_dataframes(books, ratings, tags, book_tags)
            
            logger.info(
                "Dataset loading completed",
                books_count=len(books),
                ratings_count=len(ratings),
                tags_count=len(tags),
                book_tags_count=len(book_tags)
            )
            
            return books, ratings, tags, book_tags
            
        except Exception as e:
            logger.error("Dataset loading failed", error=str(e), exc_info=True)
            raise DataLoadError(f"Error loading datasets: {str(e)}") from e
    
    async def _read_sql_async(self, conn: aiosqlite.Connection, query: str) -> pd.DataFrame:
        """Read SQL query result into pandas DataFrame asynchronously."""
        cursor = await conn.execute(query)
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return pd.DataFrame(rows, columns=columns)
    
    def _validate_dataframes(self, *dataframes: pd.DataFrame) -> None:
        """Validate that DataFrames are not empty and have expected structure."""
        df_names = ['books', 'ratings', 'tags', 'book_tags']
        
        for df, name in zip(dataframes, df_names):
            if df.empty:
                raise DataLoadError(f"{name} DataFrame is empty")
        
        # Check required columns
        required_columns = {
            'books': ['book_id', 'title'],
            'ratings': ['user_id', 'book_id', 'rating'],
            'tags': ['tag_id', 'tag_name'],
            'book_tags': ['goodreads_book_id', 'tag_id']  # Note: uses goodreads_book_id
        }
        
        for df, name in zip(dataframes, df_names):
            missing_cols = set(required_columns[name]) - set(df.columns)
            if missing_cols:
                raise DataLoadError(f"{name} missing required columns: {missing_cols}")
    
    async def merge_book_metadata_async(
        self, 
        books: pd.DataFrame, 
        book_tags: pd.DataFrame, 
        tags: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Merge books with their tags asynchronously.
        
        Args:
            books: Books DataFrame
            book_tags: Book-tag relationships DataFrame
            tags: Tags DataFrame
            
        Returns:
            Merged DataFrame with book metadata and tags
            
        Raises:
            DataLoadError: If merging fails
        """
        try:
            logger.info("Starting async book metadata merge")
            
            if self.source_type == "db":
                async with self.get_async_connection() as conn:
                    merged_books = await self._read_sql_async(conn, """
                        SELECT b.*, bt.*, t.tag_name 
                        FROM books b
                        LEFT JOIN book_tags bt ON b.goodreads_book_id = bt.goodreads_book_id
                        LEFT JOIN tags t ON bt.tag_id = t.tag_id
                    """)
                    return merged_books
            
            # For file-based sources, use async merge operations
            loop = asyncio.get_event_loop()
            
            # Merge book_tags with tags first
            book_tags_merged = await loop.run_in_executor(
                self._executor,
                lambda: book_tags.merge(tags, on='tag_id', how='left')
            )
            
            # Then merge with books
            merged_books = await loop.run_in_executor(
                self._executor,
                lambda: books.merge(
                    book_tags_merged,
                    left_on='goodreads_book_id',
                    right_on='goodreads_book_id',
                    how='left'
                )
            )
            
            logger.info("Book metadata merge completed", merged_count=len(merged_books))
            return merged_books
            
        except Exception as e:
            logger.error("Book metadata merge failed", error=str(e))
            raise DataLoadError(f"Error merging book metadata: {str(e)}") from e
    
    async def preprocess_tags_async(self, books: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess book tags for feature extraction asynchronously.
        
        Args:
            books: Books DataFrame with tag information
            
        Returns:
            DataFrame with preprocessed 'all_tags' column
            
        Raises:
            DataLoadError: If preprocessing fails
        """
        try:
            logger.info("Starting async tag preprocessing")
            
            if self.source_type == "db":
                async with self.get_async_connection() as conn:
                    all_tags_df = await self._read_sql_async(conn, """
                        SELECT b.book_id, GROUP_CONCAT(t.tag_name, ' ') as all_tags
                        FROM books b
                        LEFT JOIN book_tags bt ON b.book_id = bt.book_id
                        LEFT JOIN tags t ON bt.tag_id = t.tag_id
                        GROUP BY b.book_id
                    """)
                    books = books.merge(all_tags_df, on='book_id', how='left')
            else:
                # For file-based sources
                loop = asyncio.get_event_loop()
                books = await loop.run_in_executor(
                    self._executor,
                    self._process_tags_groupby,
                    books
                )
            
            # Clean up and deduplicate
            books = books.drop_duplicates(subset='book_id')
            books.loc[:, 'all_tags'] = books['all_tags'].fillna('')
            
            logger.info("Tag preprocessing completed", num_books=len(books))
            return books
            
        except Exception as e:
            logger.error("Tag preprocessing failed", error=str(e))
            raise DataLoadError(f"Error preprocessing tags: {str(e)}") from e
    
    def _process_tags_groupby(self, books: pd.DataFrame) -> pd.DataFrame:
        """Helper method to process tags groupby operation."""
        books = books.copy()
        books['all_tags'] = books.groupby('book_id')['tag_name'].transform(
            lambda x: ' '.join(x.dropna())
        )
        return books
    
    async def get_user_ratings_async(
        self, 
        ratings: Optional[pd.DataFrame] = None, 
        user_id: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get ratings for a specific user asynchronously.
        
        Args:
            ratings: Optional ratings DataFrame (will load if not provided)
            user_id: User ID to filter ratings for
            
        Returns:
            DataFrame with user's ratings
            
        Raises:
            DataLoadError: If user ratings retrieval fails
        """
        try:
            if user_id is None:
                raise DataLoadError("user_id must be provided")
            
            logger.info("Getting user ratings", user_id=user_id)
            
            if self.source_type == "db":
                async with self.get_async_connection() as conn:
                    user_ratings = await self._read_sql_async(
                        conn,
                        f"SELECT * FROM ratings WHERE user_id = {user_id}"
                    )
                    return user_ratings
            
            if ratings is None:
                _, ratings, _, _ = await self.load_datasets_async()
            
            # Filter user ratings asynchronously
            loop = asyncio.get_event_loop()
            user_ratings = await loop.run_in_executor(
                self._executor,
                lambda: ratings[ratings['user_id'] == user_id]
            )
            
            logger.info("User ratings retrieved", user_id=user_id, rating_count=len(user_ratings))
            return user_ratings
            
        except Exception as e:
            logger.error("Failed to get user ratings", user_id=user_id, error=str(e))
            raise DataLoadError(f"Error getting user ratings: {str(e)}") from e
    
    async def get_book_metadata_async(self, book_id: int) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific book asynchronously.
        
        Args:
            book_id: Book ID to get metadata for
            
        Returns:
            Dictionary with book metadata or None if not found
        """
        try:
            if self.source_type == "db":
                async with self.get_async_connection() as conn:
                    result = await self._read_sql_async(
                        conn,
                        f"SELECT * FROM books WHERE book_id = {book_id}"
                    )
                    return result.iloc[0].to_dict() if not result.empty else None
            
            books, _, _, _ = await self.load_datasets_async()
            book_data = books[books['book_id'] == book_id]
            return book_data.iloc[0].to_dict() if not book_data.empty else None
            
        except Exception as e:
            logger.error("Failed to get book metadata", book_id=book_id, error=str(e))
            return None
    
    def __del__(self):
        """Cleanup thread pool executor."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)