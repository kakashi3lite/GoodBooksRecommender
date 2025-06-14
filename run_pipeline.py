import os
import logging
import argparse
from pathlib import Path
from datetime import datetime

from scripts.prepare_data import DataPreparation
from scripts.train_model import ModelTrainer
from scripts.monitor_performance import PerformanceMonitor
from src.config import Config

# Set up logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Run the GoodBooks Recommender pipeline')
    parser.add_argument(
        '--steps',
        nargs='+',
        choices=['prepare', 'train', 'monitor'],
        default=['prepare', 'train', 'monitor'],
        help='Pipeline steps to run'
    )
    parser.add_argument(
        '--force-download',
        action='store_true',
        help='Force download of datasets even if they exist'
    )
    return parser.parse_args()

def run_pipeline(args):
    """Run the complete pipeline or specified steps."""
    try:
        config = Config()
        start_time = datetime.now()
        logger.info(f"Starting pipeline with steps: {args.steps}")
        
        # Step 1: Data Preparation
        if 'prepare' in args.steps:
            logger.info("\n=== Starting Data Preparation ===")
            data_prep = DataPreparation()
            if args.force_download:
                # Remove existing data files if force download is requested
                for file in data_prep.files.values():
                    file_path = data_prep.data_dir / file
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(f"Removed existing file: {file}")
            
            data_prep.prepare_datasets()
            logger.info("Data preparation completed successfully")
        
        # Step 2: Model Training
        if 'train' in args.steps:
            logger.info("\n=== Starting Model Training ===")
            trainer = ModelTrainer()
            trainer.train()
            logger.info("Model training completed successfully")
        
        # Step 3: Performance Monitoring
        if 'monitor' in args.steps:
            logger.info("\n=== Starting Performance Monitoring ===")
            monitor = PerformanceMonitor()
            monitor.generate_performance_report()
            logger.info("Performance monitoring completed successfully")
        
        # Log pipeline completion
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"\nPipeline completed successfully in {duration}")
        logger.info("Summary of artifacts created:")
        
        if 'prepare' in args.steps:
            logger.info(f"- Data files in: {config.DATA_DIR}")
        if 'train' in args.steps:
            logger.info(f"- Model files in: {config.MODEL_DIR}")
        if 'monitor' in args.steps:
            logger.info(f"- Performance reports in: {config.REPORTS_DIR}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

def main():
    try:
        args = parse_arguments()
        run_pipeline(args)
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()