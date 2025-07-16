#!/usr/bin/env python3
"""
Production Monitoring Stack Deployment and Validation Script
Deploys and validates the complete monitoring infrastructure for GoodBooks Recommender.
"""

import asyncio
import json
import logging
import os
import subprocess
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonitoringDeployment:
    """Deploy and validate the monitoring stack."""
    
    def __init__(self):
        self.services = {
            "goodbooks-api": {"url": "http://localhost:8000/health", "critical": True},
            "postgres": {"url": "http://localhost:5432", "critical": True, "tcp_check": True},
            "redis": {"url": "http://localhost:6379", "critical": True, "tcp_check": True},
            "prometheus": {"url": "http://localhost:9090/api/v1/status/config", "critical": True},
            "alertmanager": {"url": "http://localhost:9093/api/v1/status", "critical": True},
            "grafana": {"url": "http://localhost:3000/api/health", "critical": True},
            "elasticsearch": {"url": "http://localhost:9200/_cluster/health", "critical": True},
            "logstash": {"url": "http://localhost:9600", "critical": False},
            "kibana": {"url": "http://localhost:5601/api/status", "critical": True},
            "jaeger": {"url": "http://localhost:16686/api/traces", "critical": True},
            "goodbooks-webhook": {"url": "http://localhost:5001/health", "critical": False}
        }
        self.deployment_status = {}
    
    def run_command(self, command: str, check: bool = True) -> Tuple[bool, str]:
        """Run a shell command and return success status and output."""
        try:
            logger.info(f"Running command: {command}")
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=check
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            return False, e.stderr
    
    def check_docker_compose_file(self) -> bool:
        """Validate that docker-compose.monitoring.yml exists and is valid."""
        compose_file = "docker-compose.monitoring.yml"
        
        if not os.path.exists(compose_file):
            logger.error(f"Docker Compose file {compose_file} not found!")
            return False
        
        # Validate compose file syntax
        success, output = self.run_command(f"docker-compose -f {compose_file} config")
        if not success:
            logger.error(f"Docker Compose file validation failed: {output}")
            return False
        
        logger.info("Docker Compose file validation passed")
        return True
    
    def setup_environment_variables(self):
        """Set up required environment variables."""
        env_vars = {
            "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
            "SLACK_CRITICAL_CHANNEL": "#alerts-critical",
            "SLACK_ALERTS_CHANNEL": "#alerts",
            "SLACK_INFO_CHANNEL": "#monitoring",
            "SLACK_TEST_CHANNEL": "#alerts-test",
            "CRITICAL_EMAIL": "admin@goodbooks-recommender.com",
            "TEAM_EMAIL": "team@goodbooks-recommender.com",
            "GRAFANA_HOST": "localhost:3000",
            "KIBANA_HOST": "localhost:5601",
            "PROMETHEUS_HOST": "localhost:9090",
            "SMTP_HOST": "smtp.gmail.com:587",
            "SMTP_FROM": "alerts@goodbooks-recommender.com",
        }
        
        # Create .env file if it doesn't exist
        env_file = ".env"
        if not os.path.exists(env_file):
            logger.info("Creating .env file with default values...")
            with open(env_file, "w") as f:
                f.write("# GoodBooks Recommender Monitoring Environment Variables\n")
                f.write("# Update these values for your environment\n\n")
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            logger.info(f"Created {env_file}. Please update with your actual values!")
        else:
            logger.info(f"Environment file {env_file} already exists")
    
    def deploy_monitoring_stack(self) -> bool:
        """Deploy the complete monitoring stack using Docker Compose."""
        logger.info("Deploying monitoring stack...")
        
        # Pull latest images first
        logger.info("Pulling latest Docker images...")
        success, output = self.run_command(
            "docker-compose -f docker-compose.monitoring.yml pull", 
            check=False
        )
        if not success:
            logger.warning(f"Some images failed to pull: {output}")
        
        # Build custom images
        logger.info("Building custom images...")
        success, output = self.run_command(
            "docker-compose -f docker-compose.monitoring.yml build", 
            check=False
        )
        if not success:
            logger.error(f"Image build failed: {output}")
            return False
        
        # Start services
        logger.info("Starting monitoring services...")
        success, output = self.run_command(
            "docker-compose -f docker-compose.monitoring.yml up -d"
        )
        if not success:
            logger.error(f"Service startup failed: {output}")
            return False
        
        logger.info("Monitoring stack deployment initiated")
        return True
    
    def wait_for_service(self, service_name: str, config: Dict, timeout: int = 300) -> bool:
        """Wait for a service to become available."""
        logger.info(f"Waiting for {service_name} to become available...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if config.get("tcp_check"):
                    # For databases, just check if port is open
                    import socket
                    host, port = "localhost", int(config["url"].split(":")[-1])
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    if result == 0:
                        logger.info(f"✅ {service_name} is available")
                        return True
                else:
                    # HTTP health check
                    response = requests.get(config["url"], timeout=10)
                    if response.status_code < 400:
                        logger.info(f"✅ {service_name} is available")
                        return True
            except Exception as e:
                logger.debug(f"{service_name} not ready yet: {e}")
            
            time.sleep(10)
        
        logger.error(f"❌ {service_name} failed to become available within {timeout}s")
        return False
    
    def validate_service_health(self, service_name: str, config: Dict) -> bool:
        """Validate that a service is healthy and responding correctly."""
        try:
            if config.get("tcp_check"):
                # For TCP services, just check connectivity
                import socket
                host, port = "localhost", int(config["url"].split(":")[-1])
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                result = sock.connect_ex((host, port))
                sock.close()
                return result == 0
            else:
                # HTTP health check with detailed validation
                response = requests.get(config["url"], timeout=15)
                
                if service_name == "prometheus":
                    # Check Prometheus configuration
                    return response.status_code == 200 and "success" in response.text.lower()
                elif service_name == "grafana":
                    # Check Grafana health
                    return response.status_code == 200
                elif service_name == "elasticsearch":
                    # Check Elasticsearch cluster health
                    data = response.json()
                    return data.get("status") in ["green", "yellow"]
                elif service_name == "alertmanager":
                    # Check Alertmanager status
                    return response.status_code == 200
                else:
                    return response.status_code < 400
                    
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            return False
    
    def validate_monitoring_integration(self) -> Dict[str, bool]:
        """Validate that monitoring components are properly integrated."""
        integration_tests = {}
        
        # Test Prometheus targets
        try:
            response = requests.get("http://localhost:9090/api/v1/targets", timeout=10)
            if response.status_code == 200:
                data = response.json()
                targets = data.get("data", {}).get("activeTargets", [])
                healthy_targets = [t for t in targets if t.get("health") == "up"]
                integration_tests["prometheus_targets"] = len(healthy_targets) > 0
                logger.info(f"Prometheus has {len(healthy_targets)} healthy targets")
            else:
                integration_tests["prometheus_targets"] = False
        except Exception as e:
            logger.error(f"Failed to check Prometheus targets: {e}")
            integration_tests["prometheus_targets"] = False
        
        # Test Grafana datasources
        try:
            # Note: This would require Grafana API key in production
            response = requests.get("http://localhost:3000/api/datasources", 
                                  auth=("admin", "admin123"), timeout=10)
            if response.status_code == 200:
                datasources = response.json()
                integration_tests["grafana_datasources"] = len(datasources) > 0
                logger.info(f"Grafana has {len(datasources)} configured datasources")
            else:
                integration_tests["grafana_datasources"] = False
        except Exception as e:
            logger.error(f"Failed to check Grafana datasources: {e}")
            integration_tests["grafana_datasources"] = False
        
        # Test Elasticsearch indices
        try:
            response = requests.get("http://localhost:9200/_cat/indices?format=json", timeout=10)
            if response.status_code == 200:
                indices = response.json()
                logstash_indices = [idx for idx in indices if "logstash" in idx.get("index", "")]
                integration_tests["elasticsearch_indices"] = len(logstash_indices) > 0
                logger.info(f"Elasticsearch has {len(logstash_indices)} Logstash indices")
            else:
                integration_tests["elasticsearch_indices"] = False
        except Exception as e:
            logger.error(f"Failed to check Elasticsearch indices: {e}")
            integration_tests["elasticsearch_indices"] = False
        
        # Test Jaeger traces
        try:
            response = requests.get("http://localhost:16686/api/services", timeout=10)
            if response.status_code == 200:
                data = response.json()
                services = data.get("data", [])
                integration_tests["jaeger_services"] = len(services) > 0
                logger.info(f"Jaeger has traces for {len(services)} services")
            else:
                integration_tests["jaeger_services"] = False
        except Exception as e:
            logger.error(f"Failed to check Jaeger services: {e}")
            integration_tests["jaeger_services"] = False
        
        return integration_tests
    
    def run_deployment_validation(self) -> bool:
        """Run complete deployment validation."""
        logger.info("Starting monitoring stack deployment validation...")
        
        # Step 1: Pre-deployment checks
        logger.info("Step 1: Pre-deployment validation...")
        if not self.check_docker_compose_file():
            return False
        
        self.setup_environment_variables()
        
        # Step 2: Deploy monitoring stack
        logger.info("Step 2: Deploying monitoring stack...")
        if not self.deploy_monitoring_stack():
            return False
        
        # Step 3: Wait for services to start
        logger.info("Step 3: Waiting for services to start...")
        all_services_ready = True
        
        for service_name, config in self.services.items():
            if not self.wait_for_service(service_name, config):
                if config.get("critical", False):
                    all_services_ready = False
                    logger.error(f"Critical service {service_name} failed to start")
                else:
                    logger.warning(f"Non-critical service {service_name} not available")
        
        if not all_services_ready:
            logger.error("Critical services failed to start properly")
            return False
        
        # Step 4: Validate service health
        logger.info("Step 4: Validating service health...")
        for service_name, config in self.services.items():
            healthy = self.validate_service_health(service_name, config)
            self.deployment_status[service_name] = healthy
            
            if healthy:
                logger.info(f"✅ {service_name} is healthy")
            else:
                status = "❌ CRITICAL" if config.get("critical", False) else "⚠️ WARNING"
                logger.error(f"{status} {service_name} health check failed")
        
        # Step 5: Validate integration
        logger.info("Step 5: Validating component integration...")
        integration_status = self.validate_monitoring_integration()
        
        # Step 6: Generate deployment report
        self.generate_deployment_report(integration_status)
        
        # Determine overall success
        critical_services = [name for name, config in self.services.items() if config.get("critical", False)]
        critical_failures = [name for name in critical_services if not self.deployment_status.get(name, False)]
        
        if critical_failures:
            logger.error(f"Deployment failed due to critical service failures: {critical_failures}")
            return False
        
        logger.info("✅ Monitoring stack deployment validation completed successfully!")
        return True
    
    def generate_deployment_report(self, integration_status: Dict[str, bool]):
        """Generate a comprehensive deployment report."""
        report = {
            "deployment_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_services": len(self.services),
                "healthy_services": sum(1 for status in self.deployment_status.values() if status),
                "failed_services": sum(1 for status in self.deployment_status.values() if not status),
                "critical_services_healthy": all(
                    self.deployment_status.get(name, False) 
                    for name, config in self.services.items() 
                    if config.get("critical", False)
                )
            },
            "service_status": self.deployment_status,
            "integration_status": integration_status,
            "access_urls": {
                "Grafana Dashboard": "http://localhost:3000 (admin/admin123)",
                "Prometheus": "http://localhost:9090",
                "Alertmanager": "http://localhost:9093",
                "Kibana": "http://localhost:5601",
                "Jaeger": "http://localhost:16686",
                "API Documentation": "http://localhost:8000/docs",
                "Alert Webhook": "http://localhost:5001/alerts/history"
            },
            "next_steps": [
                "Update Slack webhook URL in .env file for real notifications",
                "Configure email SMTP settings for alert notifications",
                "Import Grafana dashboards for application monitoring",
                "Set up log retention policies in Elasticsearch",
                "Test alert notifications using scripts/test_alerts.py",
                "Configure PagerDuty integration for critical alerts",
                "Set up automated backups for monitoring data"
            ]
        }
        
        # Save report
        report_file = f"monitoring_deployment_report_{int(time.time())}.json"
        with open(report_file, "w") as f:
            json.dump(report, indent=2, fp=f)
        
        logger.info(f"Deployment report saved to {report_file}")
        
        # Print summary
        print("\n" + "="*70)
        print("MONITORING STACK DEPLOYMENT SUMMARY")
        print("="*70)
        print(f"Total Services: {report['deployment_summary']['total_services']}")
        print(f"Healthy Services: {report['deployment_summary']['healthy_services']}")
        print(f"Failed Services: {report['deployment_summary']['failed_services']}")
        print(f"Critical Services Status: {'✅ ALL HEALTHY' if report['deployment_summary']['critical_services_healthy'] else '❌ FAILURES DETECTED'}")
        
        print("\nSERVICE STATUS:")
        for service, status in self.deployment_status.items():
            icon = "✅" if status else "❌"
            print(f"  {icon} {service}")
        
        print("\nINTEGRATION STATUS:")
        for integration, status in integration_status.items():
            icon = "✅" if status else "❌"
            print(f"  {icon} {integration}")
        
        print("\nACCESS URLS:")
        for name, url in report["access_urls"].items():
            print(f"  • {name}: {url}")
        
        print("\nNEXT STEPS:")
        for step in report["next_steps"]:
            print(f"  • {step}")
        
        print("="*70)

def main():
    """Main deployment function."""
    print("GoodBooks Recommender - Production Monitoring Deployment")
    print("="*60)
    
    deployer = MonitoringDeployment()
    
    success = deployer.run_deployment_validation()
    
    if success:
        print("\n🎉 Monitoring stack deployed successfully!")
        print("Access Grafana at http://localhost:3000 (admin/admin123)")
        print("Run 'python scripts/test_alerts.py' to test alerting")
    else:
        print("\n❌ Deployment validation failed!")
        print("Check the logs above for details and retry")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
