"""
Enhanced Features Deployment Script

This script handles the deployment and configuration of all enhanced features
for the GoodBooks Recommender system.
"""

import asyncio
import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List
import yaml

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.logging import StructuredLogger
except ImportError:
    # Fallback logger for development
    import logging
    
    class StructuredLogger:
        def __init__(self, name):
            self.logger = logging.getLogger(name)
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        def info(self, msg): self.logger.info(msg)
        def error(self, msg): self.logger.error(msg)
        def warning(self, msg): self.logger.warning(msg)

logger = StructuredLogger(__name__)


class EnhancedFeaturesDeployment:
    """Deployment manager for enhanced features."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.project_root = Path(__file__).parent.parent
        self.config = self._load_deployment_config()
        
    def _load_deployment_config(self) -> Dict[str, Any]:
        """Load deployment configuration."""
        config_file = self.project_root / "config" / f"deployment_{self.environment}.yml"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Default configuration
            return {
                "redis": {
                    "host": "localhost",
                    "port": 6379,
                    "password": None
                },
                "features": {
                    "analytics": {"enabled": True},
                    "cache": {"enabled": True},
                    "health": {"enabled": True},
                    "batch_processing": {"enabled": True},
                    "ab_testing": {"enabled": True},
                    "performance_monitoring": {"enabled": True},
                    "model_optimization": {"enabled": True}
                }
            }
    
    async def deploy_all(self) -> bool:
        """Deploy all enhanced features."""
        logger.info(f"Starting enhanced features deployment for {self.environment} environment...")
        
        try:
            # Check prerequisites
            if not await self._check_prerequisites():
                return False
            
            # Create configuration files
            await self._create_configuration_files()
            
            # Setup Redis
            if not await self._setup_redis():
                return False
            
            # Deploy individual features
            deployment_steps = [
                ("analytics", self._deploy_analytics),
                ("cache", self._deploy_cache),
                ("health_monitoring", self._deploy_health_monitoring),
                ("batch_processing", self._deploy_batch_processing),
                ("ab_testing", self._deploy_ab_testing),
                ("performance_monitoring", self._deploy_performance_monitoring),
                ("model_optimization", self._deploy_model_optimization)
            ]
            
            for feature_name, deploy_func in deployment_steps:
                if self.config["features"].get(feature_name, {}).get("enabled", True):
                    logger.info(f"Deploying {feature_name}...")
                    if not await deploy_func():
                        logger.error(f"Failed to deploy {feature_name}")
                        return False
                    logger.info(f"Successfully deployed {feature_name}")
                else:
                    logger.info(f"Skipping {feature_name} (disabled in configuration)")
            
            # Update main application
            await self._update_main_application()
            
            # Create systemd services (for production)
            if self.environment == "production":
                await self._create_systemd_services()
            
            # Setup monitoring
            await self._setup_monitoring()
            
            # Run post-deployment validation
            if not await self._run_validation():
                logger.warning("Some validation checks failed")
            
            logger.info("Enhanced features deployment completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            return False
    
    async def _check_prerequisites(self) -> bool:
        """Check deployment prerequisites."""
        logger.info("Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 9):
            logger.error("Python 3.9 or higher is required")
            return False
        
        # Check required packages
        required_packages = [
            "fastapi", "uvicorn", "redis", "pydantic", "numpy", "asyncio"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing required packages: {missing_packages}")
            logger.info("Run: pip install -r requirements.txt")
            return False
        
        # Check Redis availability
        try:
            # Try to import and test Redis
            try:
                import redis
            except ImportError:
                logger.error("Redis package not available. Install with: pip install redis")
                return False
                
            r = redis.Redis(
                host=self.config["redis"]["host"],
                port=self.config["redis"]["port"],
                password=self.config["redis"]["password"]
            )
            r.ping()
            logger.info("Redis connection successful")
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            return False
        
        logger.info("All prerequisites met")
        return True
    
    async def _create_configuration_files(self):
        """Create configuration files for enhanced features."""
        logger.info("Creating configuration files...")
        
        config_dir = self.project_root / "config"
        config_dir.mkdir(exist_ok=True)
        
        # Enhanced features configuration
        enhanced_config = {
            "analytics": {
                "redis_url": f"redis://{self.config['redis']['host']}:{self.config['redis']['port']}",
                "batch_size": 100,
                "flush_interval": 30,
                "retention_hours": 24
            },
            "cache": {
                "redis_url": f"redis://{self.config['redis']['host']}:{self.config['redis']['port']}",
                "l1_cache_size": 1000,
                "l1_cache_ttl": 300,
                "default_ttl": 3600,
                "warming_enabled": True
            },
            "health": {
                "check_interval": 30,
                "alert_threshold": 0.8,
                "dependency_timeout": 10.0
            },
            "batch_processing": {
                "redis_url": f"redis://{self.config['redis']['host']}:{self.config['redis']['port']}",
                "max_workers": 4,
                "queue_maxsize": 1000,
                "result_ttl": 3600
            },
            "ab_testing": {
                "redis_url": f"redis://{self.config['redis']['host']}:{self.config['redis']['port']}",
                "experiment_config_path": str(config_dir / "ab_experiments.yml")
            },
            "performance_monitoring": {
                "metrics_window_size": 1000,
                "alert_thresholds": {
                    "accuracy": 0.8,
                    "latency_ms": 500,
                    "error_rate": 0.05
                }
            },
            "model_optimization": {
                "strategies": ["hyperparameter_tuning", "feature_selection"],
                "auto_retrain_threshold": 0.1,
                "optimization_interval_hours": 24
            }
        }
        
        with open(config_dir / "enhanced_features.yml", 'w') as f:
            yaml.dump(enhanced_config, f, default_flow_style=False)
        
        # A/B testing experiments configuration
        ab_experiments = {
            "experiments": [
                {
                    "name": "recommendation_algorithm_comparison",
                    "description": "Compare collaborative filtering vs hybrid approach",
                    "variants": [
                        {"name": "control", "model_id": "collaborative_filter_v1"},
                        {"name": "treatment", "model_id": "hybrid_model_v2"}
                    ],
                    "traffic_split": {"control": 0.5, "treatment": 0.5},
                    "success_metrics": ["ctr", "conversion_rate"],
                    "minimum_sample_size": 1000,
                    "max_duration_days": 30
                }
            ]
        }
        
        with open(config_dir / "ab_experiments.yml", 'w') as f:
            yaml.dump(ab_experiments, f, default_flow_style=False)
        
        logger.info("Configuration files created")
    
    async def _setup_redis(self) -> bool:
        """Setup Redis for enhanced features."""
        logger.info("Setting up Redis...")
        
        try:
            # Test Redis connection
            try:
                import redis
            except ImportError:
                logger.error("Redis package not available. Install with: pip install redis")
                return False
                
            r = redis.Redis(
                host=self.config["redis"]["host"],
                port=self.config["redis"]["port"],
                password=self.config["redis"]["password"]
            )
            
            # Create Redis keys for different features
            namespaces = [
                "analytics:", "cache:", "health:", "batch:", 
                "ab_testing:", "performance:", "optimization:"
            ]
            
            for namespace in namespaces:
                r.set(f"{namespace}initialized", "true", ex=3600)
            
            logger.info("Redis setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Redis setup failed: {str(e)}")
            return False
    
    async def _deploy_analytics(self) -> bool:
        """Deploy real-time analytics."""
        # Analytics is already implemented, just verify
        try:
            from src.analytics.real_time_analytics import RealTimeAnalytics
            logger.info("Real-time analytics module verified")
            return True
        except ImportError as e:
            logger.error(f"Analytics deployment failed: {str(e)}")
            return False
    
    async def _deploy_cache(self) -> bool:
        """Deploy advanced caching."""
        try:
            from src.core.advanced_cache import MultiLevelCache
            logger.info("Advanced cache module verified")
            return True
        except ImportError as e:
            logger.error(f"Cache deployment failed: {str(e)}")
            return False
    
    async def _deploy_health_monitoring(self) -> bool:
        """Deploy enhanced health monitoring."""
        try:
            from src.core.enhanced_health import HealthMonitor
            logger.info("Enhanced health monitoring module verified")
            return True
        except ImportError as e:
            logger.error(f"Health monitoring deployment failed: {str(e)}")
            return False
    
    async def _deploy_batch_processing(self) -> bool:
        """Deploy batch processing engine."""
        try:
            from src.core.batch_processing import BatchProcessingEngine
            logger.info("Batch processing engine module verified")
            return True
        except ImportError as e:
            logger.error(f"Batch processing deployment failed: {str(e)}")
            return False
    
    async def _deploy_ab_testing(self) -> bool:
        """Deploy ML A/B testing framework."""
        try:
            from src.models.ab_testing import MLABTester
            logger.info("ML A/B testing framework module verified")
            return True
        except ImportError as e:
            logger.error(f"A/B testing deployment failed: {str(e)}")
            return False
    
    async def _deploy_performance_monitoring(self) -> bool:
        """Deploy model performance monitoring."""
        try:
            from src.models.model_performance import ModelPerformanceMonitor
            logger.info("Model performance monitoring module verified")
            return True
        except ImportError as e:
            logger.error(f"Performance monitoring deployment failed: {str(e)}")
            return False
    
    async def _deploy_model_optimization(self) -> bool:
        """Deploy model optimization system."""
        try:
            from src.models.model_optimization import ModelOptimizer
            logger.info("Model optimization system module verified")
            return True
        except ImportError as e:
            logger.error(f"Model optimization deployment failed: {str(e)}")
            return False
    
    async def _update_main_application(self):
        """Update main application to include enhanced features."""
        logger.info("Updating main application...")
        
        main_py_path = self.project_root / "src" / "api" / "main.py"
        
        # Read current main.py
        with open(main_py_path, 'r') as f:
            content = f.read()
        
        # Check if enhanced features integration is already present
        if "EnhancedFeaturesManager" not in content:
            # Add import and integration
            integration_code = """
# Enhanced Features Integration
from src.api.integration import EnhancedFeaturesManager

# Initialize enhanced features manager
enhanced_features_manager = EnhancedFeaturesManager()

# Add to startup event
@app.on_event("startup")
async def startup_enhanced_features():
    global enhanced_features_manager
    try:
        await enhanced_features_manager.initialize_all(app)
        logger.info("Enhanced features initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize enhanced features: {str(e)}")

# Add to shutdown event
@app.on_event("shutdown")
async def shutdown_enhanced_features():
    global enhanced_features_manager
    try:
        await enhanced_features_manager.cleanup()
        logger.info("Enhanced features cleanup completed")
    except Exception as e:
        logger.error(f"Enhanced features cleanup failed: {str(e)}")
"""
            
            # Find the right place to insert (after existing imports)
            import_section_end = content.find("# FastAPI application")
            if import_section_end != -1:
                content = (content[:import_section_end] + 
                          integration_code + "\n" + 
                          content[import_section_end:])
                
                # Write updated content
                with open(main_py_path, 'w') as f:
                    f.write(content)
                
                logger.info("Main application updated with enhanced features")
            else:
                logger.warning("Could not automatically update main application")
        else:
            logger.info("Enhanced features integration already present in main application")
    
    async def _create_systemd_services(self):
        """Create systemd services for production deployment."""
        if self.environment != "production":
            return
        
        logger.info("Creating systemd services...")
        
        service_config = f"""[Unit]
Description=GoodBooks Recommender API with Enhanced Features
After=network.target redis.service

[Service]
Type=exec
User=goodbooks
Group=goodbooks
WorkingDirectory={self.project_root}
Environment=PATH={self.project_root}/venv/bin
Environment=ENVIRONMENT=production
ExecStart={self.project_root}/venv/bin/python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
        
        service_file = "/etc/systemd/system/goodbooks-recommender.service"
        
        try:
            with open(service_file, 'w') as f:
                f.write(service_config)
            
            # Reload systemd and enable service
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "enable", "goodbooks-recommender"], check=True)
            
            logger.info("Systemd service created and enabled")
            
        except Exception as e:
            logger.error(f"Failed to create systemd service: {str(e)}")
    
    async def _setup_monitoring(self):
        """Setup monitoring for enhanced features."""
        logger.info("Setting up monitoring...")
        
        # Create Prometheus configuration
        prometheus_config = {
            "global": {
                "scrape_interval": "15s"
            },
            "scrape_configs": [
                {
                    "job_name": "goodbooks-api",
                    "static_configs": [
                        {"targets": ["localhost:8000"]}
                    ],
                    "metrics_path": "/metrics"
                }
            ]
        }
        
        monitoring_dir = self.project_root / "monitoring"
        monitoring_dir.mkdir(exist_ok=True)
        
        with open(monitoring_dir / "prometheus.yml", 'w') as f:
            yaml.dump(prometheus_config, f, default_flow_style=False)
        
        # Create Grafana dashboard configurations
        dashboard_configs = [
            "enhanced_features_overview.json",
            "analytics_dashboard.json",
            "cache_performance.json",
            "health_monitoring.json"
        ]
        
        dashboards_dir = monitoring_dir / "grafana" / "dashboards"
        dashboards_dir.mkdir(parents=True, exist_ok=True)
        
        for dashboard in dashboard_configs:
            dashboard_config = {
                "dashboard": {
                    "title": dashboard.replace(".json", "").replace("_", " ").title(),
                    "panels": [
                        {
                            "title": "Sample Panel",
                            "type": "graph",
                            "targets": [
                                {"expr": "rate(http_requests_total[5m])"}
                            ]
                        }
                    ]
                }
            }
            
            with open(dashboards_dir / dashboard, 'w') as f:
                json.dump(dashboard_config, f, indent=2)
        
        logger.info("Monitoring setup completed")
    
    async def _run_validation(self) -> bool:
        """Run post-deployment validation."""
        logger.info("Running post-deployment validation...")
        
        try:
            # Import and run validation script
            validation_script = self.project_root / "scripts" / "validate_enhanced_features.py"
            
            if validation_script.exists():
                result = subprocess.run([
                    sys.executable, str(validation_script)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("Validation completed successfully")
                    return True
                else:
                    logger.error(f"Validation failed: {result.stderr}")
                    return False
            else:
                logger.warning("Validation script not found, skipping validation")
                return True
                
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False
    
    def print_deployment_summary(self):
        """Print deployment summary."""
        print("\n" + "="*60)
        print("ENHANCED FEATURES DEPLOYMENT SUMMARY")
        print("="*60)
        print(f"Environment: {self.environment}")
        print(f"Project Root: {self.project_root}")
        print("\nDeployed Features:")
        
        for feature, config in self.config["features"].items():
            status = "✅ Enabled" if config.get("enabled", True) else "❌ Disabled"
            print(f"  {feature.ljust(25)} {status}")
        
        print(f"\nRedis Configuration:")
        print(f"  Host: {self.config['redis']['host']}")
        print(f"  Port: {self.config['redis']['port']}")
        
        print(f"\nNext Steps:")
        print(f"  1. Start the application: python -m uvicorn src.api.main:app --reload")
        print(f"  2. Access API docs: http://localhost:8000/docs")
        print(f"  3. Test enhanced endpoints: http://localhost:8000/api/v2/")
        print(f"  4. Monitor metrics: http://localhost:8000/metrics")
        print(f"  5. Run validation: python scripts/validate_enhanced_features.py")
        print("="*60)


async def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy enhanced features for GoodBooks Recommender")
    parser.add_argument("--environment", "-e", default="development", 
                       choices=["development", "staging", "production"],
                       help="Deployment environment")
    parser.add_argument("--skip-validation", action="store_true",
                       help="Skip post-deployment validation")
    
    args = parser.parse_args()
    
    deployment = EnhancedFeaturesDeployment(environment=args.environment)
    
    print(f"🚀 Deploying enhanced features for {args.environment} environment...")
    
    success = await deployment.deploy_all()
    
    if success:
        deployment.print_deployment_summary()
        print("✅ Deployment completed successfully!")
        sys.exit(0)
    else:
        print("❌ Deployment failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
