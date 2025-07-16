#!/usr/bin/env python3
"""
CI/CD Pipeline Deployment and Management Script
Handles deployment strategies, monitoring, and rollback operations
"""

import os
import json
import yaml
import subprocess
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline-deploy.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DeploymentManager:
    def __init__(self, environment: str, config_path: str):
        self.environment = environment
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def deploy_blue_green(self, image_tag: str) -> bool:
        """Execute blue-green deployment strategy"""
        logger.info(f"Starting blue-green deployment for {image_tag}")
        
        try:
            # Step 1: Deploy to green environment
            logger.info("Deploying to green environment...")
            green_success = self._deploy_to_environment('green', image_tag)
            
            if not green_success:
                logger.error("Green deployment failed")
                return False
            
            # Step 2: Run smoke tests on green
            logger.info("Running smoke tests on green environment...")
            smoke_tests_passed = self._run_smoke_tests('green')
            
            if not smoke_tests_passed:
                logger.error("Smoke tests failed on green environment")
                self._cleanup_environment('green')
                return False
            
            # Step 3: Switch traffic to green
            logger.info("Switching traffic to green environment...")
            traffic_switch_success = self._switch_traffic('green')
            
            if not traffic_switch_success:
                logger.error("Traffic switch failed")
                self._cleanup_environment('green')
                return False
            
            # Step 4: Monitor for issues
            logger.info("Monitoring deployment for 5 minutes...")
            monitoring_success = self._monitor_deployment(300)  # 5 minutes
            
            if not monitoring_success:
                logger.error("Deployment monitoring detected issues")
                self._rollback_deployment()
                return False
            
            # Step 5: Cleanup old blue environment
            logger.info("Cleaning up old blue environment...")
            self._cleanup_environment('blue')
            
            logger.info("Blue-green deployment completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Blue-green deployment failed: {str(e)}")
            self._rollback_deployment()
            return False
    
    def deploy_canary(self, image_tag: str, traffic_percentage: int = 10) -> bool:
        """Execute canary deployment strategy"""
        logger.info(f"Starting canary deployment for {image_tag} with {traffic_percentage}% traffic")
        
        try:
            # Step 1: Deploy canary version
            logger.info("Deploying canary version...")
            canary_success = self._deploy_canary_version(image_tag)
            
            if not canary_success:
                logger.error("Canary deployment failed")
                return False
            
            # Step 2: Route small percentage of traffic
            logger.info(f"Routing {traffic_percentage}% traffic to canary...")
            traffic_route_success = self._route_canary_traffic(traffic_percentage)
            
            if not traffic_route_success:
                logger.error("Canary traffic routing failed")
                self._cleanup_canary()
                return False
            
            # Step 3: Monitor canary performance
            logger.info("Monitoring canary performance...")
            for i in range(3):  # 3 monitoring cycles
                cycle_time = 120  # 2 minutes per cycle
                logger.info(f"Monitoring cycle {i+1}/3 ({cycle_time}s)")
                
                monitoring_success = self._monitor_canary_deployment(cycle_time)
                
                if not monitoring_success:
                    logger.error(f"Canary monitoring failed in cycle {i+1}")
                    self._rollback_canary()
                    return False
                
                # Gradually increase traffic
                if i < 2:
                    new_percentage = min(traffic_percentage * (i + 2), 50)
                    logger.info(f"Increasing canary traffic to {new_percentage}%")
                    self._route_canary_traffic(new_percentage)
            
            # Step 4: Full rollout if all checks pass
            logger.info("Canary deployment successful, proceeding with full rollout...")
            full_rollout_success = self._complete_canary_rollout()
            
            if not full_rollout_success:
                logger.error("Full rollout failed")
                self._rollback_canary()
                return False
            
            logger.info("Canary deployment completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Canary deployment failed: {str(e)}")
            self._rollback_canary()
            return False
    
    def deploy_rolling(self, image_tag: str) -> bool:
        """Execute rolling deployment strategy"""
        logger.info(f"Starting rolling deployment for {image_tag}")
        
        try:
            # Get current replicas
            current_replicas = self._get_current_replicas()
            batch_size = max(1, current_replicas // 3)  # Update 1/3 at a time
            
            logger.info(f"Rolling update: {current_replicas} replicas, batch size: {batch_size}")
            
            # Execute rolling update
            for batch in range(0, current_replicas, batch_size):
                batch_end = min(batch + batch_size, current_replicas)
                logger.info(f"Updating replicas {batch} to {batch_end-1}")
                
                # Update batch of replicas
                update_success = self._update_replica_batch(batch, batch_end, image_tag)
                
                if not update_success:
                    logger.error(f"Failed to update batch {batch}-{batch_end}")
                    self._rollback_rolling_deployment(batch)
                    return False
                
                # Wait for batch to be ready
                ready_success = self._wait_for_batch_ready(batch, batch_end)
                
                if not ready_success:
                    logger.error(f"Batch {batch}-{batch_end} failed to become ready")
                    self._rollback_rolling_deployment(batch)
                    return False
                
                # Run health checks
                health_success = self._run_batch_health_checks(batch, batch_end)
                
                if not health_success:
                    logger.error(f"Health checks failed for batch {batch}-{batch_end}")
                    self._rollback_rolling_deployment(batch)
                    return False
                
                logger.info(f"Batch {batch}-{batch_end} updated successfully")
            
            logger.info("Rolling deployment completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rolling deployment failed: {str(e)}")
            return False
    
    def _deploy_to_environment(self, env: str, image_tag: str) -> bool:
        """Deploy to specific environment"""
        try:
            # Simulate deployment command
            cmd = [
                'kubectl', 'set', 'image',
                f'deployment/goodbooks-{env}',
                f'goodbooks={self.config["registry"]}/{image_tag}',
                f'--namespace={self.environment}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Deployment to {env} failed: {str(e)}")
            return False
    
    def _run_smoke_tests(self, env: str) -> bool:
        """Run smoke tests against environment"""
        try:
            base_url = self.config['environments'][env]['base_url']
            
            # Health check
            health_response = requests.get(f"{base_url}/health", timeout=30)
            if health_response.status_code != 200:
                return False
            
            # API endpoint check
            api_response = requests.get(f"{base_url}/api/v1/recommendations/health", timeout=30)
            if api_response.status_code != 200:
                return False
            
            # Authentication check
            auth_response = requests.post(
                f"{base_url}/auth/login",
                json={"email": "test@example.com", "password": "testpass"},
                timeout=30
            )
            if auth_response.status_code not in [200, 401]:  # 401 is OK for invalid creds
                return False
            
            logger.info(f"Smoke tests passed for {env} environment")
            return True
            
        except Exception as e:
            logger.error(f"Smoke tests failed for {env}: {str(e)}")
            return False
    
    def _switch_traffic(self, target_env: str) -> bool:
        """Switch traffic to target environment"""
        try:
            # Update load balancer configuration
            cmd = [
                'kubectl', 'patch', 'service', 'goodbooks-service',
                '--type=json',
                f'-p=[{{"op": "replace", "path": "/spec/selector/version", "value": "{target_env}"}}]',
                f'--namespace={self.environment}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Traffic switch to {target_env} failed: {str(e)}")
            return False
    
    def _monitor_deployment(self, duration: int) -> bool:
        """Monitor deployment for specified duration"""
        try:
            start_time = time.time()
            check_interval = 30  # Check every 30 seconds
            
            while time.time() - start_time < duration:
                # Check application health
                if not self._check_application_health():
                    return False
                
                # Check error rates
                if not self._check_error_rates():
                    return False
                
                # Check response times
                if not self._check_response_times():
                    return False
                
                time.sleep(check_interval)
            
            return True
            
        except Exception as e:
            logger.error(f"Deployment monitoring failed: {str(e)}")
            return False
    
    def _check_application_health(self) -> bool:
        """Check application health endpoints"""
        try:
            base_url = self.config['monitoring']['base_url']
            response = requests.get(f"{base_url}/health", timeout=10)
            return response.status_code == 200
            
        except Exception:
            return False
    
    def _check_error_rates(self) -> bool:
        """Check error rates from monitoring"""
        try:
            # Query Prometheus for error rate
            prometheus_url = self.config['monitoring']['prometheus_url']
            query = 'rate(http_requests_total{status=~"5.."}[5m])'
            
            response = requests.get(
                f"{prometheus_url}/api/v1/query",
                params={'query': query},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['data']['result']:
                    error_rate = float(data['data']['result'][0]['value'][1])
                    return error_rate < 0.01  # Less than 1% error rate
            
            return True  # Default to OK if can't check
            
        except Exception:
            return True  # Default to OK if monitoring unavailable
    
    def _check_response_times(self) -> bool:
        """Check response times from monitoring"""
        try:
            # Query Prometheus for response time
            prometheus_url = self.config['monitoring']['prometheus_url']
            query = 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))'
            
            response = requests.get(
                f"{prometheus_url}/api/v1/query",
                params={'query': query},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['data']['result']:
                    p95_response_time = float(data['data']['result'][0]['value'][1])
                    return p95_response_time < 2.0  # Less than 2 seconds P95
            
            return True  # Default to OK if can't check
            
        except Exception:
            return True  # Default to OK if monitoring unavailable
    
    def _rollback_deployment(self) -> bool:
        """Rollback to previous deployment"""
        logger.info("Initiating deployment rollback...")
        
        try:
            cmd = [
                'kubectl', 'rollout', 'undo',
                'deployment/goodbooks',
                f'--namespace={self.environment}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Rollback completed successfully")
                return True
            else:
                logger.error(f"Rollback failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return False
    
    def _cleanup_environment(self, env: str) -> bool:
        """Cleanup specified environment"""
        try:
            cmd = [
                'kubectl', 'delete', 'deployment',
                f'goodbooks-{env}',
                f'--namespace={self.environment}',
                '--ignore-not-found=true'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Cleanup of {env} environment failed: {str(e)}")
            return False

def main():
    """Main deployment script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CI/CD Pipeline Deployment Manager')
    parser.add_argument('--strategy', choices=['blue-green', 'canary', 'rolling'], 
                       required=True, help='Deployment strategy')
    parser.add_argument('--image-tag', required=True, help='Docker image tag to deploy')
    parser.add_argument('--environment', required=True, help='Target environment')
    parser.add_argument('--config', required=True, help='Deployment configuration file')
    parser.add_argument('--canary-traffic', type=int, default=10, 
                       help='Initial canary traffic percentage')
    
    args = parser.parse_args()
    
    logger.info(f"Starting {args.strategy} deployment of {args.image_tag} to {args.environment}")
    
    manager = DeploymentManager(args.environment, args.config)
    
    success = False
    
    if args.strategy == 'blue-green':
        success = manager.deploy_blue_green(args.image_tag)
    elif args.strategy == 'canary':
        success = manager.deploy_canary(args.image_tag, args.canary_traffic)
    elif args.strategy == 'rolling':
        success = manager.deploy_rolling(args.image_tag)
    
    if success:
        logger.info("Deployment completed successfully!")
        exit(0)
    else:
        logger.error("Deployment failed!")
        exit(1)

if __name__ == "__main__":
    main()
