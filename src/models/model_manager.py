import os
import json
import pickle
import logging
from typing import Dict, Any, Optional, List
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