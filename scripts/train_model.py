import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import train_test_split

from src.data.data_loader import DataLoader
from src.models.hybrid_recommender import HybridRecommender
from src.config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self):
        self.config = Config()
        self.data_loader = DataLoader()
        self.model = None
        self.metrics = {}
        
        # Create model directory if it doesn't exist
        self.model_dir = Path(self.config.MODEL_DIR)
        self.model_dir.mkdir(parents=True, exist_ok=True)
    
    def load_data(self):
        """Load and prepare data for training."""
        try:
            logger.info("Loading datasets...")
            books_df, ratings_df, tags_df = self.data_loader.load_datasets()
            
            # Merge book metadata with tags
            books_with_tags = self.data_loader.merge_book_metadata(books_df, tags_df)
            
            logger.info(f"Loaded {len(books_with_tags)} books and {len(ratings_df)} ratings")
            return books_with_tags, ratings_df
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
    
    def split_data(self, ratings_df):
        """Split ratings data into train and test sets."""
        try:
            train_data, test_data = train_test_split(
                ratings_df,
                test_size=self.config.TEST_SIZE,
                random_state=self.config.RANDOM_SEED
            )
            
            logger.info(f"Train set size: {len(train_data)}, Test set size: {len(test_data)}")
            return train_data, test_data
            
        except Exception as e:
            logger.error(f"Error splitting data: {str(e)}")
            raise
    
    def evaluate_model(self, test_data):
        """Evaluate model performance on test data."""
        try:
            predictions = []
            actuals = []
            
            for _, row in test_data.iterrows():
                pred = self.model.predict(user_id=row['user_id'], book_id=row['book_id'])
                predictions.append(pred)
                actuals.append(row['rating'])
            
            predictions = np.array(predictions)
            actuals = np.array(actuals)
            
            # Calculate metrics
            mse = np.mean((predictions - actuals) ** 2)
            rmse = np.sqrt(mse)
            mae = np.mean(np.abs(predictions - actuals))
            
            self.metrics = {
                'mse': float(mse),
                'rmse': float(rmse),
                'mae': float(mae)
            }
            
            logger.info(f"Model Evaluation Metrics: {json.dumps(self.metrics, indent=2)}")
            return self.metrics
            
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            raise
    
    def save_model(self):
        """Save trained model and metrics."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            model_path = self.model_dir / f'model_{timestamp}.pkl'
            metrics_path = self.model_dir / f'metrics_{timestamp}.json'
            
            # Save model
            self.model.save(model_path)
            
            # Save metrics
            with open(metrics_path, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'metrics': self.metrics,
                    'config': self.config.get_training_params()
                }, f, indent=2)
            
            logger.info(f"Model saved to {model_path}")
            logger.info(f"Metrics saved to {metrics_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    def train(self):
        """Train the recommender model."""
        try:
            # Load and prepare data
            books_df, ratings_df = self.load_data()
            train_data, test_data = self.split_data(ratings_df)
            
            # Initialize model
            logger.info("Initializing hybrid recommender model...")
            self.model = HybridRecommender(
                content_weight=self.config.CONTENT_WEIGHT,
                n_factors=self.config.N_FACTORS,
                n_epochs=self.config.N_EPOCHS,
                learning_rate=self.config.LEARNING_RATE
            )
            
            # Train model
            logger.info("Training model...")
            self.model.fit(books_df, train_data)
            
            # Evaluate model
            logger.info("Evaluating model...")
            self.evaluate_model(test_data)
            
            # Save model and metrics
            self.save_model()
            
            logger.info("Model training completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during model training: {str(e)}")
            raise

if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.train()