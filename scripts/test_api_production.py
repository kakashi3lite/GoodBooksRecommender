#!/usr/bin/env python3
"""
Production-grade testing script for GoodBooks Recommender API
Follows Bookworm AI Coding Standards for comprehensive validation
"""

import asyncio
import json
import time
import requests
import sys
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
import argparse


class APITester:
    """Comprehensive API testing suite for production validation."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        # Set default headers
        if self.api_key:
            self.session.headers.update({"X-API-Key": self.api_key})
        
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "response_times": [],
            "start_time": time.time()
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp and level."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        color_codes = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m",
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "RESET": "\033[0m"
        }
        
        color = color_codes.get(level, color_codes["INFO"])
        reset = color_codes["RESET"]
        print(f"{color}[{timestamp}] {level}: {message}{reset}")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with timing and error handling."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            duration = time.time() - start_time
            self.results["response_times"].append(duration)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            self.results["response_times"].append(duration)
            self.log(f"Request failed: {str(e)}", "ERROR")
            raise
    
    def test_endpoint(self, name: str, method: str, endpoint: str, 
                     expected_status: int = 200, **kwargs) -> bool:
        """Test a single endpoint."""
        try:
            self.log(f"Testing {name}...")
            response = self.make_request(method, endpoint, **kwargs)
            
            if response.status_code == expected_status:
                self.log(f"✓ {name} passed (status: {response.status_code})", "SUCCESS")
                self.results["passed"] += 1
                return True
            else:
                self.log(f"✗ {name} failed (expected: {expected_status}, got: {response.status_code})", "ERROR")
                self.results["failed"] += 1
                self.results["errors"].append(f"{name}: Status {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"✗ {name} error: {str(e)}", "ERROR")
            self.results["failed"] += 1
            self.results["errors"].append(f"{name}: {str(e)}")
            return False
    
    def test_health_endpoints(self):
        """Test health and status endpoints."""
        self.log("=== Testing Health Endpoints ===")
        
        # Root endpoint
        self.test_endpoint("Root endpoint", "GET", "/")
        
        # Health check
        self.test_endpoint("Health check", "GET", "/health")
        
        # Metrics (if enabled)
        try:
            response = self.make_request("GET", "/metrics")
            if response.status_code == 200:
                self.log("✓ Metrics endpoint accessible", "SUCCESS")
                self.results["passed"] += 1
            elif response.status_code == 404:
                self.log("⚠ Metrics endpoint disabled", "WARNING")
            else:
                self.log(f"✗ Metrics endpoint error: {response.status_code}", "ERROR")
                self.results["failed"] += 1
        except Exception as e:
            self.log(f"✗ Metrics endpoint error: {str(e)}", "ERROR")
            self.results["failed"] += 1
    
    def test_recommendation_endpoints(self):
        """Test recommendation functionality."""
        self.log("=== Testing Recommendation Endpoints ===")
        
        # Test user-based recommendations
        user_payload = {
            "user_id": 1,
            "n_recommendations": 5,
            "include_explanation": True
        }
        
        response = self.make_request("POST", "/recommendations", json=user_payload)
        if response.status_code == 200:
            data = response.json()
            if "recommendations" in data and len(data["recommendations"]) > 0:
                self.log("✓ User-based recommendations working", "SUCCESS")
                self.results["passed"] += 1
                
                # Validate response structure
                rec = data["recommendations"][0]
                required_fields = ["title", "authors", "average_rating", "hybrid_score"]
                if all(field in rec for field in required_fields):
                    self.log("✓ Recommendation response structure valid", "SUCCESS")
                    self.results["passed"] += 1
                else:
                    self.log("✗ Recommendation response structure invalid", "ERROR")
                    self.results["failed"] += 1
            else:
                self.log("✗ No recommendations returned", "ERROR")
                self.results["failed"] += 1
        else:
            self.log(f"✗ User recommendations failed: {response.status_code}", "ERROR")
            self.results["failed"] += 1
        
        # Test content-based recommendations
        content_payload = {
            "book_title": "Harry Potter",
            "n_recommendations": 3,
            "include_explanation": False
        }
        
        self.test_endpoint(
            "Content-based recommendations",
            "POST",
            "/recommendations",
            json=content_payload
        )
        
        # Test invalid requests
        invalid_payload = {"n_recommendations": 5}  # Missing both user_id and book_title
        
        self.test_endpoint(
            "Invalid request validation",
            "POST",
            "/recommendations",
            expected_status=400,
            json=invalid_payload
        )
    
    def test_performance(self, concurrent_requests: int = 10):
        """Test API performance under load."""
        self.log("=== Testing Performance ===")
        
        def make_test_request():
            try:
                payload = {"user_id": 1, "n_recommendations": 5}
                response = self.make_request("POST", "/recommendations", json=payload)
                return response.status_code == 200
            except:
                return False
        
        # Concurrent requests test
        self.log(f"Testing {concurrent_requests} concurrent requests...")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(make_test_request) for _ in range(concurrent_requests)]
            results = [future.result() for future in futures]
        
        duration = time.time() - start_time
        success_rate = sum(results) / len(results) * 100
        
        self.log(f"Concurrent requests completed in {duration:.2f}s", "INFO")
        self.log(f"Success rate: {success_rate:.1f}%", "INFO")
        
        if success_rate >= 95:
            self.log("✓ Performance test passed", "SUCCESS")
            self.results["passed"] += 1
        else:
            self.log("✗ Performance test failed", "ERROR")
            self.results["failed"] += 1
    
    def test_caching(self):
        """Test caching functionality."""
        self.log("=== Testing Caching ===")
        
        payload = {"user_id": 1, "n_recommendations": 5}
        
        # First request (cache miss)
        start_time = time.time()
        response1 = self.make_request("POST", "/recommendations", json=payload)
        first_duration = time.time() - start_time
        
        if response1.status_code == 200:
            data1 = response1.json()
            
            # Second request (should be cache hit)
            start_time = time.time()
            response2 = self.make_request("POST", "/recommendations", json=payload)
            second_duration = time.time() - start_time
            
            if response2.status_code == 200:
                data2 = response2.json()
                
                # Check if second request was faster (indicating cache hit)
                if second_duration < first_duration * 0.8:  # 20% faster
                    self.log("✓ Caching appears to be working", "SUCCESS")
                    self.results["passed"] += 1
                else:
                    self.log("⚠ Cache performance improvement not detected", "WARNING")
                
                # Check cache_hit flag if present
                if "cache_hit" in data2 and data2["cache_hit"]:
                    self.log("✓ Cache hit flag detected", "SUCCESS")
                    self.results["passed"] += 1
                else:
                    self.log("⚠ Cache hit flag not found or false", "WARNING")
            else:
                self.log("✗ Second request failed", "ERROR")
                self.results["failed"] += 1
        else:
            self.log("✗ First request failed", "ERROR")
            self.results["failed"] += 1
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        self.log("=== Testing Edge Cases ===")
        
        # Test large n_recommendations
        self.test_endpoint(
            "Large n_recommendations",
            "POST",
            "/recommendations",
            json={"user_id": 1, "n_recommendations": 50}
        )
        
        # Test invalid user_id
        self.test_endpoint(
            "Invalid user_id",
            "POST",
            "/recommendations",
            expected_status=422,  # Validation error
            json={"user_id": -1, "n_recommendations": 5}
        )
        
        # Test empty book_title
        self.test_endpoint(
            "Empty book_title",
            "POST",
            "/recommendations",
            expected_status=422,  # Validation error
            json={"book_title": "", "n_recommendations": 5}
        )
        
        # Test very long book_title
        long_title = "a" * 1000
        self.test_endpoint(
            "Very long book_title",
            "POST",
            "/recommendations",
            json={"book_title": long_title, "n_recommendations": 5}
        )
    
    def run_all_tests(self, include_performance: bool = True):
        """Run all test suites."""
        self.log("🚀 Starting GoodBooks API Test Suite")
        self.log(f"Testing against: {self.base_url}")
        
        try:
            # Test API availability
            response = self.make_request("GET", "/")
            if response.status_code != 200:
                self.log("API is not accessible. Aborting tests.", "ERROR")
                return False
            
            # Run test suites
            self.test_health_endpoints()
            self.test_recommendation_endpoints()
            self.test_caching()
            self.test_edge_cases()
            
            if include_performance:
                self.test_performance()
            
            # Calculate statistics
            total_tests = self.results["passed"] + self.results["failed"]
            success_rate = (self.results["passed"] / total_tests * 100) if total_tests > 0 else 0
            avg_response_time = sum(self.results["response_times"]) / len(self.results["response_times"])
            total_duration = time.time() - self.results["start_time"]
            
            # Print summary
            self.log("=== Test Summary ===")
            self.log(f"Total tests: {total_tests}")
            self.log(f"Passed: {self.results['passed']}")
            self.log(f"Failed: {self.results['failed']}")
            self.log(f"Success rate: {success_rate:.1f}%")
            self.log(f"Average response time: {avg_response_time:.3f}s")
            self.log(f"Total duration: {total_duration:.2f}s")
            
            if self.results["errors"]:
                self.log("Errors encountered:")
                for error in self.results["errors"]:
                    self.log(f"  - {error}", "ERROR")
            
            if success_rate >= 90:
                self.log("🎉 API is ready for production!", "SUCCESS")
                return True
            else:
                self.log("❌ API has issues that need to be addressed", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Test suite failed: {str(e)}", "ERROR")
            return False


def main():
    parser = argparse.ArgumentParser(description="Test GoodBooks Recommender API")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--no-performance", action="store_true", help="Skip performance tests")
    parser.add_argument("--concurrent", type=int, default=10, help="Number of concurrent requests for performance test")
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = APITester(args.url, args.api_key)
    
    # Run tests
    success = tester.run_all_tests(include_performance=not args.no_performance)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
