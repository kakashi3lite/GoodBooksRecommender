import os
import pandas as pd
import requests
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm

class DataPreparation:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / 'data'
        self.data_dir.mkdir(exist_ok=True)
        
        self.files = {
            'books': 'books.csv',
            'ratings': 'ratings.csv',
            'tags': 'tags.csv',
            'book_tags': 'book_tags.csv'
        }
        
        # Goodreads dataset URLs (example URLs, replace with actual dataset sources)
        self.urls = {
            'books': 'https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/books.csv',
            'ratings': 'https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/ratings.csv',
            'tags': 'https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/tags.csv',
            'book_tags': 'https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/book_tags.csv'
        }
    
    def download_file(self, url: str, filename: str) -> None:
        """Download a file from URL with progress bar."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            
            with open(self.data_dir / filename, 'wb') as f:
                with tqdm(total=total_size, unit='iB', unit_scale=True) as pbar:
                    for data in response.iter_content(block_size):
                        size = f.write(data)
                        pbar.update(size)
                        
            print(f"Successfully downloaded {filename}")
            
        except Exception as e:
            print(f"Error downloading {filename}: {str(e)}")
    
    def clean_books_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess books data."""
        try:
            # Remove duplicates
            df = df.drop_duplicates(subset='goodreads_book_id')
            
            # Clean text columns
            text_columns = ['title', 'authors', 'isbn', 'isbn13', 'language_code']
            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            
            # Convert ratings to float
            numeric_columns = ['average_rating', 'ratings_count', 'work_ratings_count']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            print(f"Error cleaning books data: {str(e)}")
            return df
    
    def clean_ratings_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess ratings data."""
        try:
            # Remove duplicates
            df = df.drop_duplicates(subset=['user_id', 'book_id'])
            
            # Convert rating to float
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
            
            # Remove invalid ratings
            df = df[df['rating'].between(1, 5)]
            
            return df
            
        except Exception as e:
            print(f"Error cleaning ratings data: {str(e)}")
            return df
    
    def clean_tags_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess tags data."""
        try:
            # Remove duplicates
            df = df.drop_duplicates(subset='tag_id')
            
            # Clean tag names
            if 'tag_name' in df.columns:
                df['tag_name'] = df['tag_name'].astype(str).str.strip().str.lower()
            
            return df
            
        except Exception as e:
            print(f"Error cleaning tags data: {str(e)}")
            return df
    
    def prepare_datasets(self) -> None:
        """Download and prepare all datasets."""
        try:
            # Download files
            for name, url in self.urls.items():
                if not (self.data_dir / self.files[name]).exists():
                    print(f"Downloading {name} dataset...")
                    self.download_file(url, self.files[name])
                else:
                    print(f"{name} dataset already exists.")
            
            # Load and clean datasets
            print("\nCleaning datasets...")
            
            # Books
            books_df = pd.read_csv(self.data_dir / self.files['books'])
            books_df = self.clean_books_data(books_df)
            books_df.to_csv(self.data_dir / self.files['books'], index=False)
            
            # Ratings
            ratings_df = pd.read_csv(self.data_dir / self.files['ratings'])
            ratings_df = self.clean_ratings_data(ratings_df)
            ratings_df.to_csv(self.data_dir / self.files['ratings'], index=False)
            
            # Tags
            tags_df = pd.read_csv(self.data_dir / self.files['tags'])
            tags_df = self.clean_tags_data(tags_df)
            tags_df.to_csv(self.data_dir / self.files['tags'], index=False)
            
            print("\nDataset preparation completed successfully!")
            
            # Print dataset statistics
            print("\nDataset Statistics:")
            print(f"Number of books: {len(books_df)}")
            print(f"Number of ratings: {len(ratings_df)}")
            print(f"Number of unique users: {ratings_df['user_id'].nunique()}")
            print(f"Number of tags: {len(tags_df)}")
            
        except Exception as e:
            print(f"Error preparing datasets: {str(e)}")

if __name__ == "__main__":
    data_prep = DataPreparation()
    data_prep.prepare_datasets()