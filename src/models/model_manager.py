import os
import json
import pickle
import logging
import threading
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from pathlib import Path
from src.config import Config
from src.models.hybrid_recommender import HybridRecommender

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self.config = Config()
        self.model_dir = Path(self.config.MODEL_DIR)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.current_model = None
        self.current_model_version = None
        
        # Dynamic loading support
        self._model_cache = {}  # Cache for multiple model versions
        self._reload_callbacks = []  # Callbacks to trigger on model reload
        self._watch_thread = None
        self._watching = False
        self._lock = threading.RLock()
        
    def register_reload_callback(self, callback: Callable[[HybridRecommender, str], None]) -> None:
        """
        Register a callback to be called when model is reloaded.
        
        Args:
            callback: Function to call with (new_model, version_id)
        """
        self._reload_callbacks.append(callback)
        
    def start_model_watching(self, check_interval: int = 60) -> None:
        """
        Start watching for new model versions and auto-reload.
        
        Args:
            check_interval: Seconds between checks for new models
        """
        if self._watching:
            return
            
        self._watching = True
        self._watch_thread = threading.Thread(
            target=self._model_watch_loop,
            args=(check_interval,),
            daemon=True
        )
        self._watch_thread.start()
        logger.info(f"Started model watching with {check_interval}s interval")
        
    def stop_model_watching(self) -> None:
        """Stop watching for model updates."""
        self._watching = False
        if self._watch_thread:
            self._watch_thread.join(timeout=5)
        logger.info("Stopped model watching")
        
    def _model_watch_loop(self, check_interval: int) -> None:
        """Background loop to check for new models."""
        while self._watching:
            try:
                latest_version = self._get_latest_version_id()
                
                if latest_version and latest_version != self.current_model_version:
                    logger.info(f"New model version detected: {latest_version}")
                    self.hot_swap_model(latest_version)
                    
            except Exception as e:
                logger.error(f"Error in model watch loop: {str(e)}")
                
            time.sleep(check_interval)
            
    def hot_swap_model(self, version_id: str) -> bool:
        """
        Hot-swap the current model with zero downtime.
        
        Args:
            version_id: Version ID of the model to swap to
            
        Returns:
            True if swap was successful
        """
        try:
            with self._lock:
                # Load new model into cache if not already loaded
                if version_id not in self._model_cache:
                    new_model = self._load_model_version(version_id)
                    self._model_cache[version_id] = new_model
                
                # Atomic swap
                old_model = self.current_model
                old_version = self.current_model_version
                
                self.current_model = self._model_cache[version_id]
                self.current_model_version = version_id
                
                # Trigger callbacks
                for callback in self._reload_callbacks:
                    try:
                        callback(self.current_model, version_id)
                    except Exception as e:
                        logger.error(f"Reload callback failed: {str(e)}")
                
                logger.info(f"Hot-swapped model from {old_version} to {version_id}")
                
                # Clean up old model cache (keep last 3 versions)
                self._cleanup_model_cache()
                
                return True
                
        except Exception as e:
            logger.error(f"Hot swap failed: {str(e)}")
            return False
            
    def _cleanup_model_cache(self) -> None:
        """Remove old models from cache to save memory."""
        if len(self._model_cache) <= 3:
            return
            
        # Get all version IDs sorted by timestamp
        versions = list(self._model_cache.keys())
        versions.sort(reverse=True)  # Newest first
        
        # Keep only the 3 most recent
        to_remove = versions[3:]
        
        for version_id in to_remove:
            if version_id != self.current_model_version:
                del self._model_cache[version_id]
                logger.debug(f"Removed model {version_id} from cache")

    def load_model_async(self, version_id: Optional[str] = None) -> HybridRecommender:
        """
        Load model asynchronously without blocking current operations.
        
        Args:
            version_id: Specific version to load, or latest if None
            
        Returns:
            Loaded model instance
        """
        target_version = version_id or self._get_latest_version_id()
        
        if not target_version:
            raise ValueError("No model versions available")
            
        # Check cache first
        if target_version in self._model_cache:
            return self._model_cache[target_version]
            
        # Load in background thread for non-blocking operation
        def load_worker():
            try:
                model = self._load_model_version(target_version)
                with self._lock:
                    self._model_cache[target_version] = model
                logger.info(f"Async loaded model {target_version}")
            except Exception as e:
                logger.error(f"Async model loading failed: {str(e)}")
                
        thread = threading.Thread(target=load_worker, daemon=True)
        thread.start()
        
        # Return current model while loading in background
        if self.current_model:
            return self.current_model
        else:
            # If no current model, wait for loading to complete
            thread.join(timeout=30)
            return self._model_cache.get(target_version)

    def deploy_model(self, 
                    model_uri: str, 
                    version: str,
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Deploy a model from MLflow URI to production.
        
        Args:
            model_uri: MLflow model URI
            version: Model version identifier
            metadata: Additional deployment metadata
            
        Returns:
            True if deployment was successful
        """
        try:
            # Import MLflow here to avoid dependency issues
            from src.core.mlflow_integration import MLflowModelRegistry
            
            registry = MLflowModelRegistry()
            model = registry.load_model(model_uri)
            
            # Save model locally for faster access
            local_version_id = f"mlflow_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            deployment_metadata = {
                'source': 'mlflow',
                'model_uri': model_uri,
                'mlflow_version': version,
                'deployment_timestamp': datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # Save using existing save_model method
            self.save_model(model, {}, deployment_metadata)
            
            # Hot swap to new model
            return self.hot_swap_model(local_version_id)
            
        except Exception as e:
            logger.error(f"Model deployment failed: {str(e)}")
            return False

    def get_model_health(self) -> Dict[str, Any]:
        """
        Get health status of current model and model manager.
        
        Returns:
            Health status information
        """
        try:
            with self._lock:
                health = {
                    'status': 'healthy' if self.current_model else 'no_model',
                    'current_version': self.current_model_version,
                    'cache_size': len(self._model_cache),
                    'watching': self._watching,
                    'last_check': datetime.now().isoformat()
                }
                
                if self.current_model:
                    # Test model with dummy prediction
                    try:
                        # This would depend on your model's interface
                        test_prediction = hasattr(self.current_model, 'predict')
                        health['model_responsive'] = test_prediction
                    except Exception:
                        health['model_responsive'] = False
                        health['status'] = 'degraded'
                
                return health
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def rollback_model(self, target_version: Optional[str] = None) -> bool:
        """
        Rollback to a previous model version.
        
        Args:
            target_version: Version to rollback to, or previous version if None
            
        Returns:
            True if rollback was successful
        """
        try:
            if target_version:
                rollback_version = target_version
            else:
                # Find previous version
                versions = self.list_model_versions()
                if len(versions) < 2:
                    logger.error("No previous version available for rollback")
                    return False
                    
                # Get second most recent version
                rollback_version = versions[1]['version_id']
            
            logger.info(f"Rolling back to model version: {rollback_version}")
            return self.hot_swap_model(rollback_version)
            
        except Exception as e:
            logger.error(f"Model rollback failed: {str(e)}")
            return False

    def _get_latest_version_id(self) -> Optional[str]:
        """Get the latest model version ID."""
        try:
            model_files = list(self.model_dir.glob('model_*.pkl'))
            if not model_files:
                return None
                
            # Sort by creation time (newest first)
            model_files.sort(key=lambda x: x.stat().st_ctime, reverse=True)
            
            # Extract version ID from filename
            latest_file = model_files[0]
            version_id = latest_file.stem.replace('model_', '')
            
            return version_id
            
        except Exception as e:
            logger.error(f"Error getting latest version: {str(e)}")
            return None
            
    def _load_model_version(self, version_id: str) -> HybridRecommender:
        """Load a specific model version from disk."""
        model_path = self.model_dir / f'model_{version_id}.pkl'
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model version {version_id} not found")
            
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
            
        logger.info(f"Loaded model version {version_id}")
        return model

    def save_model(self, model: HybridRecommender, metrics: Dict[str, float], params: Dict[str, Any]) -> str:
        """Save model, metrics, and parameters with versioning."""
        try:
            # Generate version ID based on timestamp
            version_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save model file
            model_path = self.model_dir / f'model_{version_id}.pkl'
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            # Save metadata
            metadata = {
                'version_id': version_id,
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics,
                'parameters': params,
                'python_version': self.config.PYTHON_VERSION,
                'dependencies': self._get_dependencies()
            }
            
            metadata_path = self.model_dir / f'metadata_{version_id}.json'
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Saved model version {version_id}")
            return version_id
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    def load_model(self, version_id: Optional[str] = None) -> HybridRecommender:
        """Load a specific model version or the latest model."""
        try:
            if version_id is None:
                # Get the latest version
                model_files = list(self.model_dir.glob('model_*.pkl'))
                if not model_files:
                    raise FileNotFoundError("No model files found")
                
                latest_model = max(model_files, key=lambda x: x.stem.split('_')[1])
                version_id = latest_model.stem.split('_')[1]
            
            model_path = self.model_dir / f'model_{version_id}.pkl'
            if not model_path.exists():
                raise FileNotFoundError(f"Model version {version_id} not found")
            
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            self.current_model = model
            self.current_model_version = version_id
            
            logger.info(f"Loaded model version {version_id}")
            return model
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def get_model_metadata(self, version_id: Optional[str] = None) -> Dict[str, Any]:
        """Get metadata for a specific model version or the latest model."""
        try:
            if version_id is None:
                metadata_files = list(self.model_dir.glob('metadata_*.json'))
                if not metadata_files:
                    raise FileNotFoundError("No metadata files found")
                
                latest_metadata = max(metadata_files, key=lambda x: x.stem.split('_')[1])
                version_id = latest_metadata.stem.split('_')[1]
            
            metadata_path = self.model_dir / f'metadata_{version_id}.json'
            if not metadata_path.exists():
                raise FileNotFoundError(f"Metadata for version {version_id} not found")
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting model metadata: {str(e)}")
            raise
    
    def list_model_versions(self) -> List[Dict[str, Any]]:
        """List all available model versions with their metadata."""
        try:
            versions = []
            metadata_files = self.model_dir.glob('metadata_*.json')
            
            for metadata_file in metadata_files:
                version_id = metadata_file.stem.split('_')[1]
                metadata = self.get_model_metadata(version_id)
                versions.append(metadata)
            
            # Sort by timestamp in descending order
            versions.sort(key=lambda x: x['timestamp'], reverse=True)
            return versions
            
        except Exception as e:
            logger.error(f"Error listing model versions: {str(e)}")
            raise
    
    def delete_model_version(self, version_id: str) -> bool:
        """Delete a specific model version and its metadata."""
        try:
            model_path = self.model_dir / f'model_{version_id}.pkl'
            metadata_path = self.model_dir / f'metadata_{version_id}.json'
            
            if not model_path.exists() or not metadata_path.exists():
                raise FileNotFoundError(f"Model version {version_id} not found")
            
            # Delete files
            model_path.unlink()
            metadata_path.unlink()
            
            logger.info(f"Deleted model version {version_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting model version: {str(e)}")
            return False
    
    def compare_versions(self, version_id_1: str, version_id_2: str) -> Dict[str, Any]:
        """Compare metrics and parameters between two model versions."""
        try:
            metadata_1 = self.get_model_metadata(version_id_1)
            metadata_2 = self.get_model_metadata(version_id_2)
            
            # Compare metrics
            metric_diff = {}
            for metric in metadata_1['metrics']:
                if metric in metadata_2['metrics']:
                    diff = metadata_1['metrics'][metric] - metadata_2['metrics'][metric]
                    pct_change = (diff / metadata_2['metrics'][metric]) * 100
                    metric_diff[metric] = {
                        'absolute_diff': diff,
                        'percentage_change': pct_change
                    }
            
            # Compare parameters
            param_diff = {}
            for param in metadata_1['parameters']:
                if param in metadata_2['parameters']:
                    if metadata_1['parameters'][param] != metadata_2['parameters'][param]:
                        param_diff[param] = {
                            'version_1': metadata_1['parameters'][param],
                            'version_2': metadata_2['parameters'][param]
                        }
            
            return {
                'version_1': version_id_1,
                'version_2': version_id_2,
                'metric_differences': metric_diff,
                'parameter_differences': param_diff
            }
            
        except Exception as e:
            logger.error(f"Error comparing model versions: {str(e)}")
            raise
    
    def _get_dependencies(self) -> Dict[str, str]:
        """Get current Python dependencies."""
        try:
            import pkg_resources
            return {pkg.key: pkg.version for pkg in pkg_resources.working_set}
        except Exception as e:
            logger.error(f"Error getting dependencies: {str(e)}")
            return {}