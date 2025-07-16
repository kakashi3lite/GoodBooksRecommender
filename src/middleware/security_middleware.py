"""
Security Middleware for Web Vulnerability Protection
Implements comprehensive security measures including CSP, input validation, and security headers.
"""

import re
import json
import time
import hashlib
from typing import Dict, Any, Optional, List, Set
from urllib.parse import unquote
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers
import bleach
from cryptography.fernet import Fernet
import redis.asyncio as redis

from src.core.settings import settings
from src.core.enhanced_logging import StructuredLogger
from src.core.monitoring import MetricsCollector

logger = StructuredLogger(__name__)
metrics = MetricsCollector()


class SecurityHeaders:
    """Security headers configuration."""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get standard security headers."""
        headers = {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            
            # XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Feature policy
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            
            # Server information hiding
            "Server": "GoodBooks/2.0",
        }
        
        # HSTS (only in production with HTTPS)
        if settings.is_production:
            headers["Strict-Transport-Security"] = f"max-age={settings.security.hsts_max_age}; includeSubDomains; preload"
        
        # Content Security Policy
        if settings.security.enable_csp:
            headers["Content-Security-Policy"] = settings.security.csp_policy
        
        return headers


class InputValidator:
    """Input validation and sanitization."""
    
    # Dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(--|;|\/\*|\*\/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\bUNION\s+SELECT\b)",
    ]
    
    XSS_PATTERNS = [
        r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",
        r"javascript:",
        r"vbscript:",
        r"on\w+\s*=",
        r"<iframe\b[^>]*>.*?<\/iframe>",
        r"<object\b[^>]*>.*?<\/object>",
        r"<embed\b[^>]*>",
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$()]",
        r"\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig|wget|curl)\b",
    ]
    
    def __init__(self):
        self.sql_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.SQL_INJECTION_PATTERNS]
        self.xss_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.XSS_PATTERNS]
        self.cmd_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.COMMAND_INJECTION_PATTERNS]
    
    def validate_input(self, value: str, field_name: str = "input") -> str:
        """Validate and sanitize input value."""
        if not isinstance(value, str):
            return value
        
        # URL decode first
        decoded_value = unquote(value)
        
        # Check for SQL injection
        if self._contains_sql_injection(decoded_value):
            logger.warning(
                "SQL injection attempt detected",
                field=field_name,
                value_preview=decoded_value[:100],
                ip="unknown"  # Will be filled by middleware
            )
            metrics.track_security_incident("sql_injection")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid input detected in {field_name}"
            )
        
        # Check for XSS
        if self._contains_xss(decoded_value):
            logger.warning(
                "XSS attempt detected",
                field=field_name,
                value_preview=decoded_value[:100],
                ip="unknown"
            )
            metrics.track_security_incident("xss")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid input detected in {field_name}"
            )
        
        # Check for command injection
        if self._contains_command_injection(decoded_value):
            logger.warning(
                "Command injection attempt detected",
                field=field_name,
                value_preview=decoded_value[:100],
                ip="unknown"
            )
            metrics.track_security_incident("command_injection")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid input detected in {field_name}"
            )
        
        # Sanitize HTML
        sanitized = bleach.clean(
            decoded_value,
            tags=[],  # No HTML tags allowed
            attributes={},
            protocols=[],
            strip=True
        )
        
        return sanitized
    
    def _contains_sql_injection(self, value: str) -> bool:
        """Check for SQL injection patterns."""
        return any(pattern.search(value) for pattern in self.sql_patterns)
    
    def _contains_xss(self, value: str) -> bool:
        """Check for XSS patterns."""
        return any(pattern.search(value) for pattern in self.xss_patterns)
    
    def _contains_command_injection(self, value: str) -> bool:
        """Check for command injection patterns."""
        return any(pattern.search(value) for pattern in self.cmd_patterns)
    
    def validate_json_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON payload recursively."""
        if isinstance(payload, dict):
            return {key: self.validate_json_payload(value) for key, value in payload.items()}
        elif isinstance(payload, list):
            return [self.validate_json_payload(item) for item in payload]
        elif isinstance(payload, str):
            return self.validate_input(payload, "json_field")
        else:
            return payload


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting middleware with sliding window."""
    
    def __init__(self, app, redis_client: redis.Redis):
        super().__init__(app)
        self.redis = redis_client
        self.default_rate_limit = settings.security.rate_limit_per_minute
        self.daily_rate_limit = settings.security.rate_limit_per_day
        self.burst_limit = settings.security.rate_limit_burst
    
    async def dispatch(self, request: Request, call_next):
        """Rate limiting logic."""
        client_ip = self._get_client_ip(request)
        endpoint = request.url.path
        
        # Check rate limits
        if await self._is_rate_limited(client_ip, endpoint):
            logger.warning(
                "Rate limit exceeded",
                ip=client_ip,
                endpoint=endpoint,
                user_agent=request.headers.get("user-agent", "unknown")
            )
            metrics.track_rate_limit_exceeded(client_ip)
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = await self._get_remaining_requests(client_ip)
        response.headers["X-RateLimit-Limit"] = str(self.default_rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def _is_rate_limited(self, client_ip: str, endpoint: str) -> bool:
        """Check if client is rate limited."""
        try:
            current_time = int(time.time())
            minute_window = current_time // 60
            day_window = current_time // 86400
            
            # Keys for different time windows
            minute_key = f"rate_limit:{client_ip}:minute:{minute_window}"
            day_key = f"rate_limit:{client_ip}:day:{day_window}"
            burst_key = f"rate_limit:{client_ip}:burst"
            
            # Use pipeline for atomic operations
            pipe = self.redis.pipeline()
            
            # Check current counts
            pipe.get(minute_key)
            pipe.get(day_key)
            pipe.get(burst_key)
            
            results = await pipe.execute()
            minute_count = int(results[0] or 0)
            day_count = int(results[1] or 0)
            burst_count = int(results[2] or 0)
            
            # Check limits
            if minute_count >= self.default_rate_limit:
                return True
            
            if day_count >= self.daily_rate_limit:
                return True
            
            if burst_count >= self.burst_limit:
                return True
            
            # Increment counters
            pipe = self.redis.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)
            pipe.incr(day_key)
            pipe.expire(day_key, 86400)
            pipe.incr(burst_key)
            pipe.expire(burst_key, 1)  # 1 second window for burst
            
            await pipe.execute()
            
            return False
            
        except Exception as e:
            logger.error("Rate limiting error", error=str(e))
            return False  # Allow request if Redis is down
    
    async def _get_remaining_requests(self, client_ip: str) -> int:
        """Get remaining requests for client."""
        try:
            current_time = int(time.time())
            minute_window = current_time // 60
            minute_key = f"rate_limit:{client_ip}:minute:{minute_window}"
            
            count = await self.redis.get(minute_key)
            return max(0, self.default_rate_limit - int(count or 0))
            
        except Exception:
            return self.default_rate_limit


class SecurityValidationMiddleware(BaseHTTPMiddleware):
    """Security validation middleware."""
    
    def __init__(self, app):
        super().__init__(app)
        self.validator = InputValidator()
        self.blocked_ips: Set[str] = set()
        self.suspicious_patterns = [
            r"\.\.\/",  # Directory traversal
            r"\/etc\/passwd",  # File inclusion
            r"\/proc\/",  # System file access
            r"<script",  # XSS attempts
            r"union.*select",  # SQL injection
            r"exec\s*\(",  # Code execution
        ]
        self.suspicious_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns]
    
    async def dispatch(self, request: Request, call_next):
        """Security validation logic."""
        client_ip = self._get_client_ip(request)
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            logger.warning("Blocked IP attempted access", ip=client_ip)
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Access denied"}
            )
        
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.security.max_request_size:
            logger.warning(
                "Request size too large",
                ip=client_ip,
                size=content_length,
                max_size=settings.security.max_request_size
            )
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"error": "Request too large"}
            )
        
        # Validate headers count
        if len(request.headers) > settings.security.max_headers:
            logger.warning(
                "Too many headers",
                ip=client_ip,
                header_count=len(request.headers),
                max_headers=settings.security.max_headers
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Too many headers"}
            )
        
        # Validate query parameters
        if len(request.query_params) > settings.security.max_query_params:
            logger.warning(
                "Too many query parameters",
                ip=client_ip,
                param_count=len(request.query_params),
                max_params=settings.security.max_query_params
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Too many query parameters"}
            )
        
        # Check for suspicious patterns in URL
        if self._contains_suspicious_patterns(str(request.url)):
            logger.warning(
                "Suspicious URL pattern detected",
                ip=client_ip,
                url=str(request.url),
                user_agent=request.headers.get("user-agent", "unknown")
            )
            metrics.track_security_incident("suspicious_url")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid request"}
            )
        
        # Validate query parameters
        try:
            for key, value in request.query_params.items():
                self.validator.validate_input(value, f"query_param_{key}")
        except HTTPException as e:
            logger.warning(
                "Invalid query parameter",
                ip=client_ip,
                param=key,
                error=str(e.detail)
            )
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.detail}
            )
        
        # Validate JSON payload if present
        if request.method in ["POST", "PUT", "PATCH"] and "application/json" in request.headers.get("content-type", ""):
            try:
                body = await request.body()
                if body:
                    payload = json.loads(body)
                    validated_payload = self.validator.validate_json_payload(payload)
                    
                    # Replace request body with validated payload
                    request._body = json.dumps(validated_payload).encode()
                    
            except json.JSONDecodeError:
                logger.warning("Invalid JSON payload", ip=client_ip)
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Invalid JSON payload"}
                )
            except HTTPException as e:
                logger.warning(
                    "Invalid JSON content",
                    ip=client_ip,
                    error=str(e.detail)
                )
                return JSONResponse(
                    status_code=e.status_code,
                    content={"error": e.detail}
                )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        if settings.security.enable_security_headers:
            security_headers = SecurityHeaders.get_security_headers()
            for header, value in security_headers.items():
                response.headers[header] = value
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _contains_suspicious_patterns(self, url: str) -> bool:
        """Check for suspicious patterns in URL."""
        return any(pattern.search(url) for pattern in self.suspicious_regex)


class DataPrivacyMiddleware(BaseHTTPMiddleware):
    """Data privacy and anonymization middleware."""
    
    def __init__(self, app):
        super().__init__(app)
        self.encryption_key = settings.security.encryption_key.encode()
        self.cipher = Fernet(self.encryption_key)
        
        # PII patterns to anonymize in logs
        self.pii_patterns = {
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'\b\d{3}-\d{3}-\d{4}\b|\b\(\d{3}\)\s*\d{3}-\d{4}\b'),
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "credit_card": re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
        }
    
    async def dispatch(self, request: Request, call_next):
        """Data privacy logic."""
        # Process request
        response = await call_next(request)
        
        # Anonymize sensitive data in response if needed
        if settings.security.enable_data_anonymization:
            # This would be implemented based on your specific needs
            pass
        
        return response
    
    def anonymize_pii(self, text: str) -> str:
        """Anonymize PII in text."""
        if not settings.security.enable_data_anonymization:
            return text
        
        anonymized = text
        for pii_type, pattern in self.pii_patterns.items():
            anonymized = pattern.sub(f"[{pii_type.upper()}_ANONYMIZED]", anonymized)
        
        return anonymized
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        if not settings.security.enable_data_encryption:
            return data
        
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error("Encryption failed", error=str(e))
            return data
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not settings.security.enable_data_encryption:
            return encrypted_data
        
        try:
            decrypted = self.cipher.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error("Decryption failed", error=str(e))
            return encrypted_data


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """Security audit and logging middleware."""
    
    def __init__(self, app, redis_client: redis.Redis):
        super().__init__(app)
        self.redis = redis_client
        self.sensitive_endpoints = {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/reset-password",
            "/api/v1/admin/",
        }
    
    async def dispatch(self, request: Request, call_next):
        """Security audit logic."""
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        
        # Log security-sensitive requests
        if any(endpoint in str(request.url) for endpoint in self.sensitive_endpoints):
            logger.info(
                "Security-sensitive request",
                ip=client_ip,
                endpoint=request.url.path,
                method=request.method,
                user_agent=request.headers.get("user-agent", "unknown"),
                timestamp=datetime.utcnow().isoformat()
            )
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        # Log failed authentication attempts
        if response.status_code == 401:
            await self._log_failed_auth(client_ip, request)
        
        # Log suspicious activity
        if response.status_code in [400, 403, 429]:
            await self._log_suspicious_activity(client_ip, request, response.status_code)
        
        # Add audit trail header
        response.headers["X-Audit-ID"] = hashlib.md5(
            f"{client_ip}{request.url.path}{start_time}".encode()
        ).hexdigest()
        
        return response
    
    async def _log_failed_auth(self, client_ip: str, request: Request):
        """Log failed authentication attempts."""
        try:
            key = f"failed_auth:{client_ip}"
            count = await self.redis.incr(key)
            await self.redis.expire(key, 3600)  # 1 hour window
            
            logger.warning(
                "Failed authentication attempt",
                ip=client_ip,
                endpoint=request.url.path,
                attempt_count=count,
                user_agent=request.headers.get("user-agent", "unknown")
            )
            
            # Alert if too many failed attempts
            if count >= 5:
                logger.critical(
                    "Multiple failed authentication attempts",
                    ip=client_ip,
                    attempt_count=count
                )
                metrics.track_security_incident("multiple_failed_auth")
        
        except Exception as e:
            logger.error("Failed to log auth attempt", error=str(e))
    
    async def _log_suspicious_activity(self, client_ip: str, request: Request, status_code: int):
        """Log suspicious activity."""
        try:
            key = f"suspicious:{client_ip}"
            count = await self.redis.incr(key)
            await self.redis.expire(key, 3600)  # 1 hour window
            
            logger.warning(
                "Suspicious activity detected",
                ip=client_ip,
                endpoint=request.url.path,
                status_code=status_code,
                activity_count=count,
                user_agent=request.headers.get("user-agent", "unknown")
            )
        
        except Exception as e:
            logger.error("Failed to log suspicious activity", error=str(e))
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
