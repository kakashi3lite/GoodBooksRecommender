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
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
    CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))  # 1 hour default
    
    # Recommendation settings
    DEFAULT_NUM_RECOMMENDATIONS = 5
    MIN_RATING_THRESHOLD = 3.5
    
    # MLflow Configuration
    MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'file:./mlruns')
    MLFLOW_EXPERIMENT_NAME = os.getenv('MLFLOW_EXPERIMENT_NAME', 'goodbooks_recommender')
    MLFLOW_S3_BUCKET = os.getenv('MLFLOW_S3_BUCKET', None)
    MLFLOW_BACKEND_STORE_URI = os.getenv('MLFLOW_BACKEND_STORE_URI', 'sqlite:///./mlflow.db')
    
    # Airflow Configuration
    AIRFLOW_HOME = os.getenv('AIRFLOW_HOME', './airflow')
    AIRFLOW_DAGS_FOLDER = os.getenv('AIRFLOW_DAGS_FOLDER', './airflow/dags')
    AIRFLOW_DB_URI = os.getenv('AIRFLOW_DB_URI', 'sqlite:///./airflow/airflow.db')
    
    # Model Management Configuration
    MODEL_DIR = os.getenv('MODEL_DIR', 'models')
    MODEL_CACHE_SIZE = int(os.getenv('MODEL_CACHE_SIZE', '3'))
    MODEL_HEALTH_CHECK_INTERVAL = int(os.getenv('MODEL_HEALTH_CHECK_INTERVAL', '300'))  # 5 minutes
    
    # A/B Testing Configuration  
    AB_TESTING_ENABLED = os.getenv('AB_TESTING_ENABLED', 'true').lower() == 'true'
    AB_TESTING_REDIS_URL = os.getenv('AB_TESTING_REDIS_URL', REDIS_URL)
    AB_TESTING_DEFAULT_SPLIT = float(os.getenv('AB_TESTING_DEFAULT_SPLIT', '0.5'))
    
    # API Configuration
    API_VERSION = os.getenv('API_VERSION', '1.0.0')
    API_METRICS_ENABLED = os.getenv('API_METRICS_ENABLED', 'true').lower() == 'true'
    API_HEALTH_CHECK_COMPONENTS = ['database', 'redis', 'vector_store', 'model_manager']
    
    # Vector Store Configuration
    VECTOR_STORE_TYPE = os.getenv('VECTOR_STORE_TYPE', 'faiss')  # faiss, milvus, pinecone
    VECTOR_STORE_SHARDING_ENABLED = os.getenv('VECTOR_STORE_SHARDING_ENABLED', 'true').lower() == 'true'
    VECTOR_STORE_SHARD_SIZE = int(os.getenv('VECTOR_STORE_SHARD_SIZE', '50000'))
    VECTOR_STORE_USE_GPU = os.getenv('VECTOR_STORE_USE_GPU', 'false').lower() == 'true'
    
    # Milvus Configuration
    MILVUS_HOST = os.getenv('MILVUS_HOST', 'localhost')
    MILVUS_PORT = int(os.getenv('MILVUS_PORT', '19530'))
    
    # Pinecone Configuration
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY', None)
    PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1-aws')
    
    # Model Management Configuration
    MODEL_WATCHING_ENABLED = os.getenv('MODEL_WATCHING_ENABLED', 'true').lower() == 'true'
    MODEL_WATCH_INTERVAL = int(os.getenv('MODEL_WATCH_INTERVAL', '300'))  # 5 minutes
    MODEL_CACHE_SIZE = int(os.getenv('MODEL_CACHE_SIZE', '3'))
    MODEL_HOT_SWAP_ENABLED = os.getenv('MODEL_HOT_SWAP_ENABLED', 'true').lower() == 'true'
    
    # Retraining Configuration
    AUTO_RETRAINING_ENABLED = os.getenv('AUTO_RETRAINING_ENABLED', 'true').lower() == 'true'
    RETRAINING_SCHEDULE_DAYS = int(os.getenv('RETRAINING_SCHEDULE_DAYS', '7'))
    RETRAINING_PERFORMANCE_THRESHOLD = float(os.getenv('RETRAINING_PERFORMANCE_THRESHOLD', '1.2'))
    RETRAINING_AGE_THRESHOLD_DAYS = int(os.getenv('RETRAINING_AGE_THRESHOLD_DAYS', '30'))
    
    # S3 Configuration (for model artifacts)
    S3_BUCKET = os.getenv('S3_BUCKET', None)
    S3_REGION = os.getenv('S3_REGION', 'us-east-1')
    S3_ACCESS_KEY_ID = os.getenv('S3_ACCESS_KEY_ID', None)
    S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY', None)
    
    # Performance and Scaling Configuration
    ASYNC_WORKERS = int(os.getenv('ASYNC_WORKERS', '4'))
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '32'))
    MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '100'))
    
    # Real-time Metrics Configuration
    REAL_TIME_METRICS_ENABLED = os.getenv('REAL_TIME_METRICS_ENABLED', 'true').lower() == 'true'
    METRICS_AGGREGATION_WINDOW_HOURS = int(os.getenv('METRICS_AGGREGATION_WINDOW_HOURS', '24'))
    METRICS_RETENTION_DAYS = int(os.getenv('METRICS_RETENTION_DAYS', '30'))
    
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
    
    def get_vector_store_config(self):
        """Get vector store configuration as a VectorStoreConfig object."""
        from src.core.distributed_vector_store import VectorStoreConfig
        
        return VectorStoreConfig(
            vector_db_type=self.VECTOR_STORE_TYPE,
            enable_sharding=self.VECTOR_STORE_SHARDING_ENABLED,
            shard_size=self.VECTOR_STORE_SHARD_SIZE,
            use_gpu=self.VECTOR_STORE_USE_GPU,
            max_workers=self.ASYNC_WORKERS,
            enable_async_operations=True
        )
    
    def get_mlflow_config(self):
        """Get MLflow configuration dictionary."""
        return {
            'tracking_uri': self.MLFLOW_TRACKING_URI,
            'experiment_name': self.MLFLOW_EXPERIMENT_NAME,
            's3_bucket': self.MLFLOW_S3_BUCKET,
            'backend_store_uri': self.MLFLOW_BACKEND_STORE_URI
        }
    
    def get_ab_testing_config(self):
        """Get A/B testing configuration dictionary."""
        return {
            'enabled': self.AB_TESTING_ENABLED,
            'redis_db': self.AB_TEST_REDIS_DB,
            'default_traffic_split': self.AB_TEST_DEFAULT_TRAFFIC_SPLIT,
            'auto_stop_threshold': self.AB_TEST_AUTO_STOP_THRESHOLD
        }
    
    def get_retraining_config(self):
        """Get model retraining configuration dictionary."""
        return {
            'enabled': self.AUTO_RETRAINING_ENABLED,
            'schedule_days': self.RETRAINING_SCHEDULE_DAYS,
            'performance_threshold': self.RETRAINING_PERFORMANCE_THRESHOLD,
            'age_threshold_days': self.RETRAINING_AGE_THRESHOLD_DAYS
        }