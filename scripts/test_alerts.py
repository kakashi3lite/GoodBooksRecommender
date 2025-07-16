#!/usr/bin/env python3
"""
Alert Testing Script for GoodBooks Recommender System
Tests alerting functionality by simulating various failure scenarios.
"""

import asyncio
import json
import logging
import time
import requests
import subprocess
import psutil
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlertTester:
    """Test various alert scenarios and verify notification delivery."""
    
    def __init__(self, 
                 api_base_url: str = "http://localhost:8000",
                 prometheus_url: str = "http://localhost:9090",
                 alertmanager_url: str = "http://localhost:9093",
                 webhook_url: str = "http://localhost:5001"):
        self.api_base_url = api_base_url
        self.prometheus_url = prometheus_url
        self.alertmanager_url = alertmanager_url
        self.webhook_url = webhook_url
        self.test_results = []
    
    async def test_api_health(self) -> Dict[str, any]:
        """Test if the API is responding."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"status": "healthy", "response": data}
                    else:
                        return {"status": "unhealthy", "code": response.status}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def simulate_high_memory_usage(self, duration: int = 60):
        """Simulate high memory usage to trigger memory alerts."""
        logger.info(f"Simulating high memory usage for {duration} seconds...")
        
        # Allocate large amounts of memory
        memory_hogs = []
        try:
            # Allocate memory in chunks
            for i in range(10):
                # Allocate 100MB chunks
                memory_hog = bytearray(100 * 1024 * 1024)
                memory_hogs.append(memory_hog)
                await asyncio.sleep(2)
                
                # Check if we've reached high memory usage
                memory_percent = psutil.virtual_memory().percent
                logger.info(f"Memory usage: {memory_percent:.1f}%")
                
                if memory_percent > 80:
                    logger.info("High memory usage achieved!")
                    break
            
            # Hold memory for the specified duration
            await asyncio.sleep(duration)
            
        finally:
            # Clean up memory
            memory_hogs.clear()
            logger.info("Memory simulation completed")
    
    async def simulate_high_cpu_usage(self, duration: int = 60):
        """Simulate high CPU usage to trigger CPU alerts."""
        logger.info(f"Simulating high CPU usage for {duration} seconds...")
        
        async def cpu_intensive_task():
            """CPU intensive task to consume CPU cycles."""
            end_time = time.time() + duration
            while time.time() < end_time:
                # Perform CPU-intensive calculations
                sum(i * i for i in range(10000))
                await asyncio.sleep(0.001)  # Small sleep to allow other coroutines
        
        # Start multiple CPU intensive tasks
        tasks = []
        cpu_count = psutil.cpu_count()
        for i in range(cpu_count):
            task = asyncio.create_task(cpu_intensive_task())
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        logger.info("CPU simulation completed")
    
    async def simulate_api_errors(self, error_count: int = 100):
        """Generate API errors to trigger error rate alerts."""
        logger.info(f"Simulating {error_count} API errors...")
        
        error_endpoints = [
            "/recommendations/nonexistent-user",
            "/books/99999999",
            "/search/invalid-query",
            "/user/invalid/ratings"
        ]
        
        async with aiohttp.ClientSession() as session:
            for i in range(error_count):
                endpoint = error_endpoints[i % len(error_endpoints)]
                try:
                    async with session.get(f"{self.api_base_url}{endpoint}") as response:
                        if response.status >= 400:
                            logger.debug(f"Generated error {response.status} for {endpoint}")
                except Exception as e:
                    logger.debug(f"Request error for {endpoint}: {str(e)}")
                
                # Space out requests to avoid overwhelming the system
                await asyncio.sleep(0.1)
        
        logger.info("API error simulation completed")
    
    async def simulate_slow_responses(self, request_count: int = 50):
        """Generate slow API responses to trigger latency alerts."""
        logger.info(f"Simulating {request_count} slow responses...")
        
        # Use endpoints that might be slower
        slow_endpoints = [
            "/recommendations/1?n_recommendations=50",
            "/search/books?query=fantasy&limit=100",
            "/analytics/user/1/full",
            "/recommendations/similar/1?n_recommendations=30"
        ]
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            for i in range(request_count):
                endpoint = slow_endpoints[i % len(slow_endpoints)]
                start_time = time.time()
                try:
                    async with session.get(f"{self.api_base_url}{endpoint}") as response:
                        duration = time.time() - start_time
                        logger.debug(f"Request to {endpoint} took {duration:.2f}s")
                except Exception as e:
                    logger.debug(f"Slow request error for {endpoint}: {str(e)}")
                
                await asyncio.sleep(0.5)
        
        logger.info("Slow response simulation completed")
    
    def simulate_disk_space_usage(self, target_usage_gb: float = 0.5):
        """Simulate high disk usage by creating temporary files."""
        logger.info(f"Simulating disk usage of {target_usage_gb}GB...")
        
        try:
            # Create large temporary file
            temp_file_path = "temp_disk_test.tmp"
            with open(temp_file_path, "wb") as f:
                # Write in 1MB chunks
                chunk_size = 1024 * 1024  # 1MB
                chunks_to_write = int(target_usage_gb * 1024)
                
                for i in range(chunks_to_write):
                    f.write(b'0' * chunk_size)
                    if i % 100 == 0:  # Log progress every 100MB
                        logger.info(f"Written {i}MB of test data...")
            
            logger.info("Disk usage simulation file created")
            
            # Keep the file for a short time to trigger alerts
            time.sleep(30)
            
        finally:
            # Clean up the temporary file
            try:
                import os
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    logger.info("Temporary disk usage file cleaned up")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {e}")
    
    async def test_service_availability(self, service_name: str, url: str) -> bool:
        """Test if a service is available and responding."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    return response.status < 400
        except Exception as e:
            logger.warning(f"Service {service_name} unavailable: {e}")
            return False
    
    async def send_test_alert(self, alert_type: str = "test"):
        """Send a direct test alert to the webhook."""
        test_alert_payload = {
            "receiver": "test-alerts",
            "status": "firing",
            "alerts": [{
                "status": "firing",
                "labels": {
                    "alertname": "ManualTestAlert",
                    "service": "goodbooks-api",
                    "severity": alert_type,
                    "instance": "test-instance",
                    "environment": "testing"
                },
                "annotations": {
                    "description": f"This is a manual {alert_type} alert sent for testing notification channels",
                    "summary": f"Manual {alert_type} test alert",
                    "runbook_url": "https://github.com/kakashi3lite/GoodBooksRecommender/docs/runbooks/test-alert.md"
                },
                "startsAt": datetime.now().isoformat(),
                "endsAt": "",
                "generatorURL": f"{self.prometheus_url}/graph"
            }],
            "groupLabels": {
                "alertname": "ManualTestAlert",
                "service": "goodbooks-api"
            },
            "commonLabels": {
                "service": "goodbooks-api",
                "environment": "testing"
            },
            "commonAnnotations": {},
            "externalURL": self.alertmanager_url,
            "version": "4",
            "groupKey": f"test-{alert_type}-{int(time.time())}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.webhook_url}/alerts",
                    json=test_alert_payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Test alert sent successfully: {result}")
                        return True
                    else:
                        logger.error(f"Failed to send test alert: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error sending test alert: {e}")
            return False
    
    async def verify_alert_delivery(self, alert_name: str, timeout: int = 60) -> bool:
        """Verify that an alert was delivered to the webhook."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.webhook_url}/alerts/history") as response:
                        if response.status == 200:
                            data = await response.json()
                            recent_alerts = data.get("recent_alerts", [])
                            
                            for alert in recent_alerts:
                                for alert_detail in alert.get("alerts", []):
                                    if alert_detail.get("alertname") == alert_name:
                                        logger.info(f"Alert {alert_name} verified in webhook history")
                                        return True
                
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.warning(f"Error checking alert delivery: {e}")
                await asyncio.sleep(5)
        
        logger.warning(f"Alert {alert_name} not found in webhook history within {timeout}s")
        return False
    
    async def run_comprehensive_test(self):
        """Run a comprehensive test of all alert scenarios."""
        logger.info("Starting comprehensive alert testing...")
        
        test_scenarios = [
            ("API Health Check", self.test_api_health()),
            ("Send Manual Test Alert", self.send_test_alert("warning")),
            ("Send Critical Test Alert", self.send_test_alert("critical")),
            ("API Error Generation", self.simulate_api_errors(50)),
            ("Slow Response Generation", self.simulate_slow_responses(20)),
        ]
        
        # Test service availability
        services = [
            ("Prometheus", f"{self.prometheus_url}/api/v1/status/config"),
            ("Alertmanager", f"{self.alertmanager_url}/api/v1/status"),
            ("Webhook", f"{self.webhook_url}/health"),
            ("API", f"{self.api_base_url}/health")
        ]
        
        logger.info("Testing service availability...")
        for service_name, service_url in services:
            available = await self.test_service_availability(service_name, service_url)
            status = "✅ Available" if available else "❌ Unavailable"
            logger.info(f"{service_name}: {status}")
        
        # Run test scenarios
        for test_name, test_coro in test_scenarios:
            logger.info(f"Running test: {test_name}")
            try:
                start_time = time.time()
                result = await test_coro
                duration = time.time() - start_time
                
                self.test_results.append({
                    "test": test_name,
                    "result": result,
                    "duration": duration,
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"✅ {test_name} completed in {duration:.2f}s")
                
            except Exception as e:
                logger.error(f"❌ {test_name} failed: {e}")
                self.test_results.append({
                    "test": test_name,
                    "result": {"error": str(e)},
                    "duration": 0,
                    "timestamp": datetime.now().isoformat()
                })
        
        # Resource intensive tests (run separately to avoid interference)
        logger.info("Running resource intensive tests...")
        
        try:
            logger.info("Testing high memory usage alerts...")
            await self.simulate_high_memory_usage(30)
            
            # Wait a bit between tests
            await asyncio.sleep(10)
            
            logger.info("Testing high CPU usage alerts...")
            await self.simulate_high_cpu_usage(30)
            
        except Exception as e:
            logger.error(f"Resource intensive test failed: {e}")
        
        # Generate test report
        self.generate_test_report()
    
    def generate_test_report(self):
        """Generate a comprehensive test report."""
        logger.info("Generating test report...")
        
        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "successful_tests": len([r for r in self.test_results if "error" not in str(r["result"])]),
                "failed_tests": len([r for r in self.test_results if "error" in str(r["result"])]),
                "total_duration": sum(r["duration"] for r in self.test_results),
                "timestamp": datetime.now().isoformat()
            },
            "test_details": self.test_results,
            "recommendations": [
                "Check Slack/email for test alert notifications",
                "Verify Grafana dashboards show metric spikes during tests",
                "Review Prometheus for fired alerts during test period",
                "Check Kibana for log entries during test scenarios",
                "Verify alert resolution notifications are sent when issues clear"
            ]
        }
        
        # Save report to file
        report_file = f"alert_test_report_{int(time.time())}.json"
        with open(report_file, "w") as f:
            json.dump(report, indent=2, fp=f)
        
        logger.info(f"Test report saved to {report_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("ALERT TESTING SUMMARY")
        print("="*60)
        print(f"Total Tests: {report['test_summary']['total_tests']}")
        print(f"Successful: {report['test_summary']['successful_tests']}")
        print(f"Failed: {report['test_summary']['failed_tests']}")
        print(f"Duration: {report['test_summary']['total_duration']:.2f}s")
        print("="*60)
        
        if report['test_summary']['failed_tests'] > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if "error" in str(result["result"]):
                    print(f"❌ {result['test']}: {result['result']}")
        
        print("\nRECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"• {rec}")
        print()

async def main():
    """Main function to run alert tests."""
    print("GoodBooks Recommender Alert Testing System")
    print("="*50)
    
    tester = AlertTester()
    
    # Run comprehensive tests
    await tester.run_comprehensive_test()
    
    print("\nAlert testing completed!")
    print("Check your notification channels (Slack, email) for test alerts.")

if __name__ == "__main__":
    asyncio.run(main())
