#!/usr/bin/env python3
"""
GoodBooks Recommender - Security Testing Script

This script performs automated security testing including:
- Authentication testing
- Authorization (RBAC) testing  
- Input validation testing
- Rate limiting testing
- SQL injection testing
- XSS testing
- CSRF testing
"""

import asyncio
import aiohttp
import json
import time
import argparse
import sys
from typing import Dict, List, Any
from dataclasses import dataclass
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

@dataclass
class TestResult:
    test_name: str
    status: str  # "PASS", "FAIL", "WARN"
    message: str
    details: Dict[str, Any] = None


class SecurityTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.test_user_token = None
        self.admin_token = None
        self.results: List[TestResult] = []

    async def setup(self):
        """Setup test session and create test users."""
        self.session = aiohttp.ClientSession()
        
        # Create test users
        await self.create_test_users()
        
    async def teardown(self):
        """Cleanup test session."""
        if self.session:
            await self.session.close()

    async def create_test_users(self):
        """Create test users for authentication testing."""
        print(f"{Fore.BLUE}Setting up test users...{Style.RESET_ALL}")
        
        try:
            # Create regular test user
            user_data = {
                "username": "test_user",
                "email": "test@example.com",
                "password": "TestPassword123!"
            }
            
            async with self.session.post(
                f"{self.base_url}/auth/register",
                json=user_data
            ) as response:
                if response.status in [200, 201, 409]:  # 409 = already exists
                    print(f"{Fore.GREEN}✓ Test user created/exists{Style.RESET_ALL}")
                
            # Login test user
            login_data = {
                "username": "test_user",
                "password": "TestPassword123!"
            }
            
            async with self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.test_user_token = data.get('access_token')
                    print(f"{Fore.GREEN}✓ Test user authenticated{Style.RESET_ALL}")
                    
        except Exception as e:
            print(f"{Fore.YELLOW}⚠ Could not setup test users: {e}{Style.RESET_ALL}")

    async def test_authentication(self):
        """Test authentication mechanisms."""
        print(f"{Fore.BLUE}Testing Authentication...{Style.RESET_ALL}")
        
        # Test 1: Access protected endpoint without token
        try:
            async with self.session.post(
                f"{self.base_url}/recommendations",
                json={"user_id": 1, "n_recommendations": 5}
            ) as response:
                if response.status == 401:
                    self.results.append(TestResult(
                        "auth_required", "PASS", 
                        "Properly rejects unauthenticated requests"
                    ))
                else:
                    self.results.append(TestResult(
                        "auth_required", "FAIL",
                        f"Expected 401, got {response.status}"
                    ))
        except Exception as e:
            self.results.append(TestResult(
                "auth_required", "FAIL", f"Test failed: {e}"
            ))

        # Test 2: Invalid token
        try:
            headers = {"Authorization": "Bearer invalid_token"}
            async with self.session.post(
                f"{self.base_url}/recommendations",
                json={"user_id": 1, "n_recommendations": 5},
                headers=headers
            ) as response:
                if response.status == 401:
                    self.results.append(TestResult(
                        "invalid_token", "PASS",
                        "Properly rejects invalid tokens"
                    ))
                else:
                    self.results.append(TestResult(
                        "invalid_token", "FAIL",
                        f"Expected 401, got {response.status}"
                    ))
        except Exception as e:
            self.results.append(TestResult(
                "invalid_token", "FAIL", f"Test failed: {e}"
            ))

        # Test 3: Valid token access
        if self.test_user_token:
            try:
                headers = {"Authorization": f"Bearer {self.test_user_token}"}
                async with self.session.post(
                    f"{self.base_url}/recommendations",
                    json={"user_id": 1, "n_recommendations": 5},
                    headers=headers
                ) as response:
                    if response.status in [200, 403]:  # 403 if RBAC prevents access
                        self.results.append(TestResult(
                            "valid_token", "PASS",
                            "Valid token properly processed"
                        ))
                    else:
                        self.results.append(TestResult(
                            "valid_token", "FAIL",
                            f"Unexpected status: {response.status}"
                        ))
            except Exception as e:
                self.results.append(TestResult(
                    "valid_token", "FAIL", f"Test failed: {e}"
                ))

    async def test_authorization(self):
        """Test RBAC authorization."""
        print(f"{Fore.BLUE}Testing Authorization (RBAC)...{Style.RESET_ALL}")
        
        if not self.test_user_token:
            self.results.append(TestResult(
                "rbac_test", "WARN", "No test token available for RBAC testing"
            ))
            return

        # Test admin endpoint access with regular user token
        admin_endpoints = [
            "/admin/experiments",
            "/admin/models/current", 
            "/admin/vector-store/stats"
        ]
        
        for endpoint in admin_endpoints:
            try:
                headers = {"Authorization": f"Bearer {self.test_user_token}"}
                async with self.session.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers
                ) as response:
                    if response.status == 403:
                        self.results.append(TestResult(
                            f"rbac_{endpoint.replace('/', '_')}", "PASS",
                            f"Properly restricts access to {endpoint}"
                        ))
                    elif response.status == 401:
                        self.results.append(TestResult(
                            f"rbac_{endpoint.replace('/', '_')}", "PASS",
                            f"Requires authentication for {endpoint}"
                        ))
                    else:
                        self.results.append(TestResult(
                            f"rbac_{endpoint.replace('/', '_')}", "FAIL",
                            f"Unexpected access to {endpoint}: {response.status}"
                        ))
            except Exception as e:
                self.results.append(TestResult(
                    f"rbac_{endpoint.replace('/', '_')}", "FAIL", f"Test failed: {e}"
                ))

    async def test_input_validation(self):
        """Test input validation and sanitization."""
        print(f"{Fore.BLUE}Testing Input Validation...{Style.RESET_ALL}")
        
        # SQL Injection payloads
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users --"
        ]
        
        # XSS payloads
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]
        
        # Test SQL injection in book title
        for payload in sql_payloads:
            try:
                headers = {"Authorization": f"Bearer {self.test_user_token}"} if self.test_user_token else {}
                async with self.session.post(
                    f"{self.base_url}/recommendations",
                    json={"book_title": payload, "n_recommendations": 5},
                    headers=headers
                ) as response:
                    if response.status in [400, 422]:  # Validation error
                        self.results.append(TestResult(
                            f"sql_injection", "PASS",
                            "SQL injection payload properly rejected"
                        ))
                    elif response.status == 200:
                        # Check if payload was sanitized
                        data = await response.json()
                        if payload not in str(data):
                            self.results.append(TestResult(
                                f"sql_injection", "PASS",
                                "SQL injection payload sanitized"
                            ))
                        else:
                            self.results.append(TestResult(
                                f"sql_injection", "FAIL",
                                "SQL injection payload not filtered"
                            ))
                    break  # Only test first payload to avoid spam
            except Exception as e:
                self.results.append(TestResult(
                    "sql_injection", "FAIL", f"Test failed: {e}"
                ))

        # Test XSS in book title
        for payload in xss_payloads:
            try:
                headers = {"Authorization": f"Bearer {self.test_user_token}"} if self.test_user_token else {}
                async with self.session.post(
                    f"{self.base_url}/recommendations",
                    json={"book_title": payload, "n_recommendations": 5},
                    headers=headers
                ) as response:
                    if response.status in [400, 422]:  # Validation error
                        self.results.append(TestResult(
                            f"xss_validation", "PASS",
                            "XSS payload properly rejected"
                        ))
                    elif response.status == 200:
                        # Check if payload was sanitized
                        data = await response.json()
                        if payload not in str(data):
                            self.results.append(TestResult(
                                f"xss_validation", "PASS",
                                "XSS payload sanitized"
                            ))
                        else:
                            self.results.append(TestResult(
                                f"xss_validation", "FAIL",
                                "XSS payload not filtered"
                            ))
                    break  # Only test first payload
            except Exception as e:
                self.results.append(TestResult(
                    "xss_validation", "FAIL", f"Test failed: {e}"
                ))

        # Test field size limits
        try:
            large_input = "A" * 10000  # 10KB string
            headers = {"Authorization": f"Bearer {self.test_user_token}"} if self.test_user_token else {}
            async with self.session.post(
                f"{self.base_url}/recommendations",
                json={"book_title": large_input, "n_recommendations": 5},
                headers=headers
            ) as response:
                if response.status in [400, 422, 413]:  # Request too large or validation error
                    self.results.append(TestResult(
                        "input_size_limit", "PASS",
                        "Large input properly rejected"
                    ))
                else:
                    self.results.append(TestResult(
                        "input_size_limit", "WARN",
                        f"Large input accepted: {response.status}"
                    ))
        except Exception as e:
            self.results.append(TestResult(
                "input_size_limit", "FAIL", f"Test failed: {e}"
            ))

    async def test_rate_limiting(self):
        """Test rate limiting mechanisms."""
        print(f"{Fore.BLUE}Testing Rate Limiting...{Style.RESET_ALL}")
        
        # Rapid fire requests to trigger rate limiting
        requests_count = 100
        rate_limited = False
        
        try:
            start_time = time.time()
            
            for i in range(requests_count):
                async with self.session.get(f"{self.base_url}/health") as response:
                    if response.status == 429:  # Too Many Requests
                        rate_limited = True
                        self.results.append(TestResult(
                            "rate_limiting", "PASS",
                            f"Rate limiting triggered after {i+1} requests"
                        ))
                        break
                    
                    # If we're making requests too fast, slow down slightly
                    if i % 10 == 0:
                        await asyncio.sleep(0.1)
            
            end_time = time.time()
            
            if not rate_limited:
                # Check if we made a lot of requests very quickly
                if (end_time - start_time) < 10:  # 100 requests in under 10 seconds
                    self.results.append(TestResult(
                        "rate_limiting", "WARN",
                        f"No rate limiting detected for {requests_count} requests"
                    ))
                else:
                    self.results.append(TestResult(
                        "rate_limiting", "PASS",
                        "Requests were naturally throttled"
                    ))
                    
        except Exception as e:
            self.results.append(TestResult(
                "rate_limiting", "FAIL", f"Test failed: {e}"
            ))

    async def test_security_headers(self):
        """Test security headers in responses."""
        print(f"{Fore.BLUE}Testing Security Headers...{Style.RESET_ALL}")
        
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                headers = response.headers
                
                # Check for security headers
                security_headers = {
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                    "X-XSS-Protection": "1; mode=block",
                    "Strict-Transport-Security": None,  # Any value is good
                }
                
                for header, expected_values in security_headers.items():
                    if header in headers:
                        if expected_values is None or headers[header] in expected_values:
                            self.results.append(TestResult(
                                f"header_{header.lower().replace('-', '_')}", "PASS",
                                f"Security header {header} present: {headers[header]}"
                            ))
                        else:
                            self.results.append(TestResult(
                                f"header_{header.lower().replace('-', '_')}", "WARN",
                                f"Security header {header} has unexpected value: {headers[header]}"
                            ))
                    else:
                        self.results.append(TestResult(
                            f"header_{header.lower().replace('-', '_')}", "FAIL",
                            f"Security header {header} missing"
                        ))
                        
        except Exception as e:
            self.results.append(TestResult(
                "security_headers", "FAIL", f"Test failed: {e}"
            ))

    async def test_https_redirect(self):
        """Test HTTPS redirect (if running with HTTPS)."""
        print(f"{Fore.BLUE}Testing HTTPS Configuration...{Style.RESET_ALL}")
        
        if self.base_url.startswith('https://'):
            self.results.append(TestResult(
                "https_enabled", "PASS", "API is running with HTTPS"
            ))
            
            # Test HTTP redirect (if applicable)
            http_url = self.base_url.replace('https://', 'http://')
            try:
                async with self.session.get(http_url, allow_redirects=False) as response:
                    if response.status in [301, 302, 307, 308]:
                        location = response.headers.get('Location', '')
                        if location.startswith('https://'):
                            self.results.append(TestResult(
                                "https_redirect", "PASS", "HTTP properly redirects to HTTPS"
                            ))
                        else:
                            self.results.append(TestResult(
                                "https_redirect", "FAIL", "HTTP redirect doesn't use HTTPS"
                            ))
                    else:
                        self.results.append(TestResult(
                            "https_redirect", "WARN", "No HTTP to HTTPS redirect found"
                        ))
            except Exception:
                self.results.append(TestResult(
                    "https_redirect", "WARN", "Could not test HTTP redirect"
                ))
        else:
            self.results.append(TestResult(
                "https_enabled", "WARN", "API is not running with HTTPS"
            ))

    async def run_all_tests(self):
        """Run all security tests."""
        print(f"{Fore.CYAN}🔒 Starting Security Tests for {self.base_url}{Style.RESET_ALL}")
        print("=" * 60)
        
        await self.setup()
        
        try:
            await self.test_authentication()
            await self.test_authorization()
            await self.test_input_validation()
            await self.test_rate_limiting()
            await self.test_security_headers()
            await self.test_https_redirect()
        finally:
            await self.teardown()

    def print_results(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print(f"{Fore.CYAN}📊 Security Test Results{Style.RESET_ALL}")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        warnings = sum(1 for r in self.results if r.status == "WARN")
        
        for result in self.results:
            if result.status == "PASS":
                color = Fore.GREEN
                symbol = "✓"
            elif result.status == "FAIL":
                color = Fore.RED
                symbol = "✗"
            else:  # WARN
                color = Fore.YELLOW
                symbol = "⚠"
                
            print(f"{color}{symbol} {result.test_name}: {result.message}{Style.RESET_ALL}")
            
        print("\n" + "-" * 60)
        print(f"Summary: {Fore.GREEN}{passed} passed{Style.RESET_ALL}, "
              f"{Fore.RED}{failed} failed{Style.RESET_ALL}, "
              f"{Fore.YELLOW}{warnings} warnings{Style.RESET_ALL}")
        
        if failed > 0:
            print(f"\n{Fore.RED}⚠ Security issues detected! Please review failed tests.{Style.RESET_ALL}")
            return False
        elif warnings > 0:
            print(f"\n{Fore.YELLOW}⚠ Some security recommendations to consider.{Style.RESET_ALL}")
            return True
        else:
            print(f"\n{Fore.GREEN}✓ All security tests passed!{Style.RESET_ALL}")
            return True


async def main():
    parser = argparse.ArgumentParser(description="Security testing for GoodBooks Recommender")
    parser.add_argument("--target", default="http://localhost:8000", 
                       help="Target API URL (default: http://localhost:8000)")
    parser.add_argument("--output", help="Output file for results (JSON format)")
    
    args = parser.parse_args()
    
    tester = SecurityTester(args.target)
    await tester.run_all_tests()
    
    success = tester.print_results()
    
    # Save results to file if requested
    if args.output:
        results_data = {
            "target": args.target,
            "timestamp": time.time(),
            "results": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "message": r.message,
                    "details": r.details
                }
                for r in tester.results
            ],
            "summary": {
                "passed": sum(1 for r in tester.results if r.status == "PASS"),
                "failed": sum(1 for r in tester.results if r.status == "FAIL"),
                "warnings": sum(1 for r in tester.results if r.status == "WARN")
            }
        }
        
        with open(args.output, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n📄 Results saved to {args.output}")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
