"""
MLflow integration for model tracking, versioning, and registry management.
Provides centralized model artifact storage and experiment tracking.
"""

import os
import logging
import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlparse

import mlflow
import mlflow.sklearn
import mlflow.pyfunc
from mlflow.tracking import MlflowClient
from mlflow.entities import ViewType
import boto3
from botocore.exceptions import NoCredentialsError

from src.config import Config
from src.models.hybrid_recommender import HybridRecommender
from src.core.exceptions import GoodBooksException

# Use standard logging to avoid conflicts with MLflow
logger = logging.getLogger(__name__)

class MLflowError(GoodBooksException):
    """Raised when MLflow operations fail"""
    pass

class MLflowModelRegistry:
    """
    MLflow-based model registry for experiment tracking and model versioning.
    Supports both local and S3-based artifact storage.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize MLflow model registry.
        
        Args:
            config: Configuration object with MLflow settings
        """
        self.config = config or Config()
        self.client = MlflowClient()
        self.experiment_name = getattr(self.config, 'MLFLOW_EXPERIMENT_NAME', 'goodbooks_recommender')
        self.s3_bucket = getattr(self.config, 'S3_BUCKET', None)
        self.tracking_uri = getattr(self.config, 'MLFLOW_TRACKING_URI', 'file:./mlruns')
        
        self._setup_mlflow()
        self._setup_experiment()
    
    def _setup_mlflow(self) -> None:
        """Configure MLflow tracking URI and artifact store."""
        try:
            # Set tracking URI
            mlflow.set_tracking_uri(self.tracking_uri)
            
            # Configure S3 artifact store if available
            if self.s3_bucket:
                try:
                    # Test S3 credentials
                    s3_client = boto3.client('s3')
                    s3_client.head_bucket(Bucket=self.s3_bucket)
                    
                    artifact_uri = f"s3://{self.s3_bucket}/mlflow-artifacts"
                    logger.info(f"S3 artifact store configured for bucket: {self.s3_bucket}")
                    
                except (NoCredentialsError, Exception) as e:
                    logger.warning(f"S3 configuration failed, using local storage: {str(e)}")
                    artifact_uri = None
            else:
                artifact_uri = None
            
            logger.info(f"MLflow tracking configured - URI: {self.tracking_uri}, Artifacts: {artifact_uri or 'local'}")
            
        except Exception as e:
            logger.error("Failed to setup MLflow", error=str(e))
            raise MLflowError(f"MLflow setup failed: {str(e)}") from e
    
    def _setup_experiment(self) -> None:
        """Create or get the MLflow experiment."""
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(
                    name=self.experiment_name,
                    artifact_location=f"s3://{self.s3_bucket}/experiments" if self.s3_bucket else None
                )
                logger.info(f"Created MLflow experiment: {self.experiment_name} (ID: {experiment_id})")
            else:
                experiment_id = experiment.experiment_id
                logger.info(f"Using existing MLflow experiment: {self.experiment_name} (ID: {experiment_id})")
            
            mlflow.set_experiment(self.experiment_name)
            
        except Exception as e:
            logger.error("Failed to setup experiment", error=str(e))
            raise MLflowError(f"Experiment setup failed: {str(e)}") from e
    
    def start_experiment_run(self, 
                           experiment_name: Optional[str] = None,
                           run_name: Optional[str] = None,
                           tags: Optional[Dict[str, str]] = None) -> str:
        """
        Start a new MLflow experiment run.
        
        Args:
            experiment_name: Name of experiment (uses default if None)
            run_name: Name for this run
            tags: Additional tags for the run
            
        Returns:
            Run ID of the started run
        """
        try:
            if experiment_name and experiment_name != self.experiment_name:
                mlflow.set_experiment(experiment_name)
            
            default_tags = {
                'project': 'goodbooks_recommender',
                'version': getattr(self.config, 'VERSION', '1.0.0'),
                'environment': getattr(self.config, 'ENVIRONMENT', 'development')
            }
            
            if tags:
                default_tags.update(tags)
            
            run = mlflow.start_run(run_name=run_name, tags=default_tags)
            
            logger.info("Started MLflow run",
                       run_id=run.info.run_id,
                       run_name=run_name,
                       experiment=experiment_name or self.experiment_name)
            
            return run.info.run_id
            
        except Exception as e:
            logger.error("Failed to start MLflow run", error=str(e))
            raise MLflowError(f"Failed to start run: {str(e)}") from e
    
    def log_model(self,
                  model: HybridRecommender,
                  model_name: str,
                  metrics: Dict[str, float],
                  parameters: Optional[Dict[str, Any]] = None,
                  artifacts_path: str = "model") -> str:
        """
        Log model to MLflow with metrics and parameters.
        
        Args:
            model: Trained model to log
            model_name: Name for the model
            metrics: Model performance metrics
            parameters: Model hyperparameters
            artifacts_path: Path within run to store artifacts
            
        Returns:
            Model URI for the logged model
        """
        try:
            if not mlflow.active_run():
                raise MLflowError("No active MLflow run. Call start_experiment_run() first.")
            
            # Log parameters
            if parameters:
                mlflow.log_params(parameters)
            
            # Log metrics
            mlflow.log_metrics(metrics)
            
            # Log model
            model_info = mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path=artifacts_path,
                registered_model_name=model_name,
                metadata={
                    'training_timestamp': datetime.now().isoformat(),
                    'framework': 'hybrid_recommender',
                    'model_type': 'collaborative_content_hybrid'
                }
            )
            
            # Log additional artifacts
            self._log_model_artifacts(model, artifacts_path)
            
            logger.info("Model logged to MLflow",
                       model_name=model_name,
                       model_uri=model_info.model_uri,
                       metrics=metrics)
            
            return model_info.model_uri
            
        except Exception as e:
            logger.error("Failed to log model", error=str(e))
            raise MLflowError(f"Model logging failed: {str(e)}") from e
    
    def _log_model_artifacts(self, model: HybridRecommender, artifacts_path: str) -> None:
        """Log additional model artifacts like feature importance, etc."""
        try:
            # Create temporary directory for artifacts
            temp_dir = Path("temp_artifacts")
            temp_dir.mkdir(exist_ok=True)
            
            # Log model configuration
            config_path = temp_dir / "model_config.json"
            with open(config_path, 'w') as f:
                json.dump({
                    'content_weight': getattr(model, 'content_weight', 0.5),
                    'n_factors': getattr(model.collab_recommender, 'n_factors', 50),
                    'n_epochs': getattr(model.collab_recommender, 'n_epochs', 20),
                    'learning_rate': getattr(model.collab_recommender, 'learning_rate', 0.01),
                }, f, indent=2)
            
            mlflow.log_artifact(str(config_path), artifacts_path)
            
            # Log model summary
            summary_path = temp_dir / "model_summary.txt"
            with open(summary_path, 'w') as f:
                f.write(f"Model Type: Hybrid Recommender\n")
                f.write(f"Training Time: {datetime.now().isoformat()}\n")
                f.write(f"Components: Collaborative + Content Filtering\n")
            
            mlflow.log_artifact(str(summary_path), artifacts_path)
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
            
        except Exception as e:
            logger.warning("Failed to log additional artifacts", error=str(e))
    
    def load_model(self, model_uri: str) -> HybridRecommender:
        """
        Load model from MLflow.
        
        Args:
            model_uri: URI of the model to load
            
        Returns:
            Loaded model instance
        """
        try:
            model = mlflow.sklearn.load_model(model_uri)
            
            logger.info("Model loaded from MLflow", model_uri=model_uri)
            return model
            
        except Exception as e:
            logger.error("Failed to load model", model_uri=model_uri, error=str(e))
            raise MLflowError(f"Model loading failed: {str(e)}") from e
    
    def register_model(self,
                      model_uri: str,
                      model_name: str,
                      stage: str = "Staging",
                      description: Optional[str] = None) -> str:
        """
        Register model in MLflow model registry.
        
        Args:
            model_uri: URI of the model to register
            model_name: Name for registered model
            stage: Stage to assign (Staging, Production, Archived)
            description: Model description
            
        Returns:
            Model version number
        """
        try:
            # Register the model
            result = mlflow.register_model(
                model_uri=model_uri,
                name=model_name,
                description=description
            )
            
            version = result.version
            
            # Transition to specified stage
            if stage != "None":
                self.client.transition_model_version_stage(
                    name=model_name,
                    version=version,
                    stage=stage,
                    archive_existing_versions=False
                )
            
            logger.info("Model registered",
                       model_name=model_name,
                       version=version,
                       stage=stage)
            
            return version
            
        except Exception as e:
            logger.error("Failed to register model", error=str(e))
            raise MLflowError(f"Model registration failed: {str(e)}") from e
    
    def get_production_model(self, model_name: str) -> Optional[HybridRecommender]:
        """
        Get the current production model.
        
        Args:
            model_name: Name of the registered model
            
        Returns:
            Production model instance or None if not found
        """
        try:
            versions = self.client.get_latest_versions(
                name=model_name,
                stages=["Production"]
            )
            
            if not versions:
                logger.warning("No production model found", model_name=model_name)
                return None
            
            latest_version = versions[0]
            model_uri = f"models:/{model_name}/{latest_version.version}"
            
            return self.load_model(model_uri)
            
        except Exception as e:
            logger.error("Failed to get production model", error=str(e))
            return None
    
    def list_model_versions(self, model_name: str) -> List[Dict[str, Any]]:
        """
        List all versions of a registered model.
        
        Args:
            model_name: Name of the registered model
            
        Returns:
            List of model version information
        """
        try:
            versions = self.client.search_model_versions(f"name='{model_name}'")
            
            version_info = []
            for version in versions:
                version_info.append({
                    'version': version.version,
                    'stage': version.current_stage,
                    'creation_timestamp': version.creation_timestamp,
                    'last_updated_timestamp': version.last_updated_timestamp,
                    'description': version.description,
                    'run_id': version.run_id,
                    'source': version.source
                })
            
            return sorted(version_info, key=lambda x: x['version'], reverse=True)
            
        except Exception as e:
            logger.error("Failed to list model versions", error=str(e))
            return []
    
    def compare_model_versions(self,
                             model_name: str,
                             version1: str,
                             version2: str) -> Dict[str, Any]:
        """
        Compare metrics between two model versions.
        
        Args:
            model_name: Name of the registered model
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            Comparison results with metrics differences
        """
        try:
            # Get run information for both versions
            v1_info = self.client.get_model_version(model_name, version1)
            v2_info = self.client.get_model_version(model_name, version2)
            
            # Get metrics from both runs
            v1_run = self.client.get_run(v1_info.run_id)
            v2_run = self.client.get_run(v2_info.run_id)
            
            v1_metrics = v1_run.data.metrics
            v2_metrics = v2_run.data.metrics
            
            # Calculate differences
            comparison = {
                'version1': version1,
                'version2': version2,
                'metric_differences': {}
            }
            
            for metric in set(v1_metrics.keys()) | set(v2_metrics.keys()):
                v1_val = v1_metrics.get(metric, 0)
                v2_val = v2_metrics.get(metric, 0)
                
                comparison['metric_differences'][metric] = {
                    'version1_value': v1_val,
                    'version2_value': v2_val,
                    'absolute_difference': v2_val - v1_val,
                    'relative_difference': ((v2_val - v1_val) / v1_val * 100) if v1_val != 0 else float('inf')
                }
            
            return comparison
            
        except Exception as e:
            logger.error("Failed to compare model versions", error=str(e))
            return {}
    
    def archive_old_runs(self, keep_last_n: int = 10) -> None:
        """
        Archive old experiment runs to save storage.
        
        Args:
            keep_last_n: Number of recent runs to keep
        """
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if not experiment:
                return
            
            # Get all runs sorted by creation time
            runs = self.client.search_runs(
                experiment_ids=[experiment.experiment_id],
                run_view_type=ViewType.ALL,
                max_results=1000,
                order_by=["attribute.start_time DESC"]
            )
            
            # Archive old runs
            runs_to_archive = runs[keep_last_n:]
            
            for run in runs_to_archive:
                if run.info.lifecycle_stage != "deleted":
                    self.client.delete_run(run.info.run_id)
                    logger.debug("Archived old run", run_id=run.info.run_id)
            
            logger.info(f"Archived {len(runs_to_archive)} old runs")
            
        except Exception as e:
            logger.error("Failed to archive old runs", error=str(e))
    
    def get_experiment_metrics(self, experiment_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get metrics from all runs in an experiment.
        
        Args:
            experiment_name: Name of experiment (uses default if None)
            
        Returns:
            List of run metrics and metadata
        """
        try:
            exp_name = experiment_name or self.experiment_name
            experiment = mlflow.get_experiment_by_name(exp_name)
            
            if not experiment:
                return []
            
            runs = self.client.search_runs(
                experiment_ids=[experiment.experiment_id],
                run_view_type=ViewType.ACTIVE_ONLY,
                max_results=100,
                order_by=["attribute.start_time DESC"]
            )
            
            metrics_data = []
            for run in runs:
                metrics_data.append({
                    'run_id': run.info.run_id,
                    'run_name': run.data.tags.get('mlflow.runName', ''),
                    'start_time': run.info.start_time,
                    'status': run.info.status,
                    'metrics': run.data.metrics,
                    'parameters': run.data.params,
                    'tags': run.data.tags
                })
            
            return metrics_data
            
        except Exception as e:
            logger.error("Failed to get experiment metrics", error=str(e))
            return []
