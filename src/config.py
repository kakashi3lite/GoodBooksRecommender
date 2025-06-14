import os
from pathlib import Path
from typing import Dict, Any

class Config:
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / 'data'
    MODELS_DIR = BASE_DIR / 'models'
    
    # Data files
    BOOKS_FILE = 'books.csv'
    RATINGS_FILE = 'ratings.csv'
    TAGS_FILE = 'tags.csv'
    BOOK_TAGS_FILE = 'book_tags.csv'
    
    # Model parameters
    MODEL_PARAMS = {
        'collaborative': {
            'n_factors': 50,
            'learning_rate': 0.01,
            'regularization': 0.02,
            'n_epochs': 20
        },
        'hybrid': {
            'content_weight': 0.5
        }
    }
    
    # API settings
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 8000))
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    
    # Cache settings
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))  # 1 hour default
    
    # Recommendation settings
    DEFAULT_NUM_RECOMMENDATIONS = 5
    MIN_RATING_THRESHOLD = 3.5
    
    @classmethod
    def get_data_paths(cls) -> Dict[str, Path]:
        """Get paths to all data files."""
        return {
            'books': cls.DATA_DIR / cls.BOOKS_FILE,
            'ratings': cls.DATA_DIR / cls.RATINGS_FILE,
            'tags': cls.DATA_DIR / cls.TAGS_FILE,
            'book_tags': cls.DATA_DIR / cls.BOOK_TAGS_FILE
        }
    
    @classmethod
    def get_model_params(cls, model_type: str) -> Dict[str, Any]:
        """Get model parameters by type."""
        return cls.MODEL_PARAMS.get(model_type, {})
    
    @classmethod
    def create_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.MODELS_DIR.mkdir(parents=True, exist_ok=True)