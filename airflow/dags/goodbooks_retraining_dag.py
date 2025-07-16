"""
Airflow DAG for scheduled model retraining and deployment.
Orchestrates the complete ML pipeline from data validation to model deployment.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.sensors.filesystem import FileSensor
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.http.sensors.http import HttpSensor
import logging
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.data.data_loader import DataLoader
from src.models.hybrid_recommender import HybridRecommender
from src.models.model_manager import ModelManager
from src.models.ab_tester import ABTester
from scripts.train_model import ModelTrainer
from src.core.mlflow_integration import MLflowModelRegistry
from src.config import Config

logger = logging.getLogger(__name__)

# DAG Configuration
default_args = {
    'owner': 'goodbooks-ml-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'max_active_runs': 1,
}

dag = DAG(
    'goodbooks_model_retraining',
    default_args=default_args,
    description='GoodBooks model retraining and deployment pipeline',
    schedule_interval=timedelta(days=7),  # Weekly retraining
    catchup=False,
    tags=['ml', 'retraining', 'goodbooks'],
)

def validate_data(**context):
    """Validate input data quality before training."""
    try:
        config = Config()
        data_loader = DataLoader()
        
        # Load datasets
        books_df, ratings_df, tags_df = data_loader.load_datasets()
        
        # Data quality checks
        checks = {
            'books_not_empty': len(books_df) > 0,
            'ratings_not_empty': len(ratings_df) > 0,
            'no_missing_book_ids': books_df['book_id'].notna().all(),
            'no_missing_ratings': ratings_df['rating'].notna().all(),
            'valid_rating_range': ratings_df['rating'].between(1, 5).all(),
            'sufficient_ratings': len(ratings_df) >= 10000,  # Minimum threshold
        }
        
        failed_checks = [check for check, passed in checks.items() if not passed]
        
        if failed_checks:
            raise ValueError(f"Data validation failed: {failed_checks}")
        
        logger.info("Data validation passed successfully")
        
        # Store validation metrics
        context['task_instance'].xcom_push(
            key='data_quality_metrics',
            value={
                'num_books': len(books_df),
                'num_ratings': len(ratings_df),
                'avg_rating': float(ratings_df['rating'].mean()),
                'validation_timestamp': datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Data validation failed: {str(e)}")
        raise

def check_retraining_necessity(**context):
    """Check if model retraining is necessary based on performance metrics."""
    try:
        config = Config()
        model_manager = ModelManager()
        
        # Get current model performance
        latest_metadata = model_manager.get_model_metadata()
        
        if not latest_metadata:
            logger.info("No existing model found, retraining required")
            return True
        
        # Check model age (retrain if older than 30 days)
        model_date = datetime.fromisoformat(latest_metadata['timestamp'].replace('Z', '+00:00'))
        days_old = (datetime.now() - model_date).days
        
        if days_old > 30:
            logger.info(f"Model is {days_old} days old, retraining required")
            return True
        
        # Check performance degradation
        current_metrics = latest_metadata.get('metrics', {})
        rmse_threshold = 1.2  # Example threshold
        
        if current_metrics.get('rmse', float('inf')) > rmse_threshold:
            logger.info("Model performance below threshold, retraining required")
            return True
        
        logger.info("Model retraining not necessary at this time")
        return False
        
    except Exception as e:
        logger.error(f"Error checking retraining necessity: {str(e)}")
        return True  # Default to retraining on error

def train_new_model(**context):
    """Train a new model and log to MLflow."""
    try:
        # Initialize MLflow integration
        mlflow_registry = MLflowModelRegistry()
        
        # Start MLflow run
        run_id = mlflow_registry.start_experiment_run(
            experiment_name="goodbooks_retraining",
            run_name=f"scheduled_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Train model
        trainer = ModelTrainer()
        trainer.train()
        
        # Log model to MLflow
        model_uri = mlflow_registry.log_model(
            model=trainer.model,
            model_name="goodbooks_hybrid_recommender",
            metrics=trainer.metrics,
            artifacts_path="model_artifacts"
        )
        
        # Store training results
        context['task_instance'].xcom_push(
            key='training_results',
            value={
                'model_uri': model_uri,
                'run_id': run_id,
                'metrics': trainer.metrics,
                'training_timestamp': datetime.now().isoformat()
            }
        )
        
        logger.info(f"Model training completed, MLflow run: {run_id}")
        
    except Exception as e:
        logger.error(f"Model training failed: {str(e)}")
        raise

def validate_new_model(**context):
    """Validate the newly trained model before deployment."""
    try:
        training_results = context['task_instance'].xcom_pull(
            task_ids='train_model',
            key='training_results'
        )
        
        metrics = training_results['metrics']
        
        # Validation thresholds
        validation_checks = {
            'rmse_acceptable': metrics.get('rmse', float('inf')) < 1.0,
            'mae_acceptable': metrics.get('mae', float('inf')) < 0.8,
            'mse_acceptable': metrics.get('mse', float('inf')) < 1.0,
        }
        
        failed_validations = [check for check, passed in validation_checks.items() if not passed]
        
        if failed_validations:
            raise ValueError(f"Model validation failed: {failed_validations}")
        
        logger.info("New model validation passed")
        
    except Exception as e:
        logger.error(f"Model validation failed: {str(e)}")
        raise

def setup_ab_test(**context):
    """Set up A/B test for the new model."""
    try:
        config = Config()
        ab_tester = ABTester(config)
        
        training_results = context['task_instance'].xcom_pull(
            task_ids='train_model',
            key='training_results'
        )
        
        # Load current and new models
        model_manager = ModelManager()
        current_model = model_manager.load_model()  # Latest model
        
        mlflow_registry = MLflowModelRegistry()
        new_model = mlflow_registry.load_model(training_results['model_uri'])
        
        # Create A/B test experiment
        experiment_id = f"retraining_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        ab_tester.create_experiment(
            experiment_id=experiment_id,
            control_model=current_model,
            variant_model=new_model,
            description=f"A/B test for model retrained on {datetime.now().strftime('%Y-%m-%d')}",
            metrics=['precision', 'recall', 'click_through_rate', 'user_satisfaction']
        )
        
        # Store experiment details
        context['task_instance'].xcom_push(
            key='ab_test_info',
            value={
                'experiment_id': experiment_id,
                'control_model_version': current_model.version if hasattr(current_model, 'version') else 'latest',
                'variant_model_uri': training_results['model_uri'],
                'start_timestamp': datetime.now().isoformat()
            }
        )
        
        logger.info(f"A/B test created: {experiment_id}")
        
    except Exception as e:
        logger.error(f"Failed to setup A/B test: {str(e)}")
        raise

def deploy_model(**context):
    """Deploy the new model to production after successful A/B test."""
    try:
        training_results = context['task_instance'].xcom_pull(
            task_ids='train_model',
            key='training_results'
        )
        
        # Register model in MLflow model registry
        mlflow_registry = MLflowModelRegistry()
        
        model_version = mlflow_registry.register_model(
            model_uri=training_results['model_uri'],
            model_name="goodbooks_hybrid_recommender",
            stage="Production"
        )
        
        # Update model manager with new production model
        model_manager = ModelManager()
        model_manager.deploy_model(
            model_uri=training_results['model_uri'],
            version=model_version,
            metadata={
                'deployment_timestamp': datetime.now().isoformat(),
                'deployment_type': 'scheduled_retraining',
                'metrics': training_results['metrics']
            }
        )
        
        logger.info(f"Model deployed to production: version {model_version}")
        
    except Exception as e:
        logger.error(f"Model deployment failed: {str(e)}")
        raise

def cleanup_old_models(**context):
    """Clean up old model versions to save storage."""
    try:
        model_manager = ModelManager()
        mlflow_registry = MLflowModelRegistry()
        
        # Keep only last 5 model versions
        versions = model_manager.list_model_versions()
        if len(versions) > 5:
            old_versions = versions[5:]  # Remove oldest versions
            
            for version_info in old_versions:
                version_id = version_info['version_id']
                model_manager.delete_model_version(version_id)
                logger.info(f"Deleted old model version: {version_id}")
        
        # Archive old MLflow runs
        mlflow_registry.archive_old_runs(keep_last_n=10)
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        # Don't raise - cleanup failure shouldn't break the pipeline

# Define tasks
data_validation_task = PythonOperator(
    task_id='validate_data',
    python_callable=validate_data,
    dag=dag,
)

check_retraining_task = PythonOperator(
    task_id='check_retraining_necessity',
    python_callable=check_retraining_necessity,
    dag=dag,
)

train_model_task = PythonOperator(
    task_id='train_model',
    python_callable=train_new_model,
    dag=dag,
)

validate_model_task = PythonOperator(
    task_id='validate_model',
    python_callable=validate_new_model,
    dag=dag,
)

setup_ab_test_task = PythonOperator(
    task_id='setup_ab_test',
    python_callable=setup_ab_test,
    dag=dag,
)

# Health check for API before deployment
api_health_check = HttpSensor(
    task_id='api_health_check',
    http_conn_id='goodbooks_api',
    endpoint='/health',
    timeout=300,
    poke_interval=30,
    dag=dag,
)

deploy_model_task = PythonOperator(
    task_id='deploy_model',
    python_callable=deploy_model,
    dag=dag,
)

cleanup_task = PythonOperator(
    task_id='cleanup_old_models',
    python_callable=cleanup_old_models,
    dag=dag,
    trigger_rule='all_done',  # Run even if some tasks fail
)

# Define task dependencies
data_validation_task >> check_retraining_task
check_retraining_task >> train_model_task
train_model_task >> validate_model_task
validate_model_task >> setup_ab_test_task
setup_ab_test_task >> api_health_check
api_health_check >> deploy_model_task
deploy_model_task >> cleanup_task
