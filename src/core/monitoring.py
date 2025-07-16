"""
Enhanced monitoring and metrics collection for production readiness.
Implements comprehensive observability following bookworm standards.
"""

import time
import logging
import uuid
from typing import Dict, Any, Optional, List
from contextvars import ContextVar
from datetime import datetime
import psutil
import asyncio
from functools import wraps

from prometheus_client import (
    Counter, Histogram, Gauge, Info, Enum,
    CollectorRegistry, multiprocess, generate_latest,
    CONTENT_TYPE_LATEST
)
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for correlation ID
correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')

# Enhanced Prometheus metrics
REGISTRY = CollectorRegistry()

# API Metrics
REQUEST_COUNT = Counter(
    'goodbooks_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)

REQUEST_DURATION = Histogram(
    'goodbooks_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=REGISTRY
)

ACTIVE_REQUESTS = Gauge(
    'goodbooks_http_requests_active',
    'Number of active HTTP requests',
    registry=REGISTRY
)

# Business Metrics
RECOMMENDATION_REQUESTS = Counter(
    'goodbooks_recommendation_requests_total',
    'Total recommendation requests',
    ['user_type', 'recommendation_type'],
    registry=REGISTRY
)

RECOMMENDATION_DURATION = Histogram(
    'goodbooks_recommendation_duration_seconds',
    'Time to generate recommendations',
    ['recommendation_type'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=REGISTRY
)

CACHE_OPERATIONS = Counter(
    'goodbooks_cache_operations_total',
    'Cache operations',
    ['operation', 'result'],
    registry=REGISTRY
)

# Model Performance Metrics
MODEL_PREDICTIONS = Counter(
    'goodbooks_model_predictions_total',
    'Total model predictions',
    ['model_name', 'model_version'],
    registry=REGISTRY
)

MODEL_ACCURACY = Gauge(
    'goodbooks_model_accuracy',
    'Model accuracy metrics',
    ['model_name', 'metric_type'],
    registry=REGISTRY
)

# System Metrics
SYSTEM_CPU_USAGE = Gauge(
    'goodbooks_system_cpu_usage_percent',
    'System CPU usage percentage',
    registry=REGISTRY
)

SYSTEM_MEMORY_USAGE = Gauge(
    'goodbooks_system_memory_usage_bytes',
    'System memory usage in bytes',
    registry=REGISTRY
)

DATABASE_CONNECTIONS = Gauge(
    'goodbooks_database_connections_active',
    'Active database connections',
    registry=REGISTRY
)

# Error Metrics
ERROR_COUNT = Counter(
    'goodbooks_errors_total',
    'Total errors by type',
    ['error_type', 'severity'],
    registry=REGISTRY
)

# A/B Testing Metrics
AB_TEST_ASSIGNMENTS = Counter(
    'goodbooks_ab_test_assignments_total',
    'A/B test assignments',
    ['experiment_id', 'variant'],
    registry=REGISTRY
)

AB_TEST_CONVERSIONS = Counter(
    'goodbooks_ab_test_conversions_total',
    'A/B test conversions',
    ['experiment_id', 'variant', 'conversion_type'],
    registry=REGISTRY
)

# Application Info
APP_INFO = Info(
    'goodbooks_app_info',
    'Application information',
    registry=REGISTRY
)

APP_HEALTH = Enum(
    'goodbooks_app_health_status',
    'Application health status',
    states=['healthy', 'degraded', 'unhealthy'],
    registry=REGISTRY
)


class MetricsCollector:
    """Centralized metrics collection and reporting."""
    
    def __init__(self):
        self.start_time = time.time()
        self._system_metrics_task: Optional[asyncio.Task] = None
        
    async def start_background_tasks(self):
        """Start background metrics collection tasks."""
        self._system_metrics_task = asyncio.create_task(
            self._collect_system_metrics()
        )
        
    async def stop_background_tasks(self):
        """Stop background metrics collection tasks."""
        if self._system_metrics_task:
            self._system_metrics_task.cancel()
            try:
                await self._system_metrics_task
            except asyncio.CancelledError:
                pass
    
    async def _collect_system_metrics(self):
        """Collect system-level metrics periodically."""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                SYSTEM_CPU_USAGE.set(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                SYSTEM_MEMORY_USAGE.set(memory.used)
                
                # Update app info
                APP_INFO.info({
                    'version': '1.0.0',
                    'environment': 'production',
                    'uptime_seconds': str(int(time.time() - self.start_time))
                })
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                logging.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(60)  # Wait longer if error occurred
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_recommendation(self, user_type: str, rec_type: str, duration: float):
        """Record recommendation metrics."""
        RECOMMENDATION_REQUESTS.labels(
            user_type=user_type,
            recommendation_type=rec_type
        ).inc()
        
        RECOMMENDATION_DURATION.labels(
            recommendation_type=rec_type
        ).observe(duration)
    
    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation metrics."""
        CACHE_OPERATIONS.labels(
            operation=operation,
            result=result
        ).inc()
    
    def record_error(self, error_type: str, severity: str = 'error'):
        """Record error metrics."""
        ERROR_COUNT.labels(
            error_type=error_type,
            severity=severity
        ).inc()
    
    def record_ab_test_assignment(self, experiment_id: str, variant: str):
        """Record A/B test assignment."""
        AB_TEST_ASSIGNMENTS.labels(
            experiment_id=experiment_id,
            variant=variant
        ).inc()
    
    def record_ab_test_conversion(self, experiment_id: str, variant: str, conversion_type: str):
        """Record A/B test conversion."""
        AB_TEST_CONVERSIONS.labels(
            experiment_id=experiment_id,
            variant=variant,
            conversion_type=conversion_type
        ).inc()
    
    def update_health_status(self, status: str):
        """Update application health status."""
        APP_HEALTH.state(status)
    
    def set_database_connections(self, count: int):
        """Set active database connections count."""
        DATABASE_CONNECTIONS.set(count)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect request metrics."""
    
    def __init__(self, app, metrics_collector: MetricsCollector):
        super().__init__(app)
        self.metrics_collector = metrics_collector
    
    async def dispatch(self, request: Request, call_next):
        """Process request and collect metrics."""
        # Generate correlation ID
        corr_id = str(uuid.uuid4())
        correlation_id.set(corr_id)
        request.state.correlation_id = corr_id
        
        # Track active requests
        ACTIVE_REQUESTS.inc()
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            self.metrics_collector.record_request(
                method=request.method,
                endpoint=self._get_endpoint_name(request),
                status_code=response.status_code,
                duration=duration
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = corr_id
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            self.metrics_collector.record_request(
                method=request.method,
                endpoint=self._get_endpoint_name(request),
                status_code=500,
                duration=duration
            )
            
            self.metrics_collector.record_error(
                error_type=type(e).__name__,
                severity='error'
            )
            
            raise
            
        finally:
            # Decrease active requests counter
            ACTIVE_REQUESTS.dec()
    
    def _get_endpoint_name(self, request: Request) -> str:
        """Extract endpoint name from request."""
        if hasattr(request, 'url') and hasattr(request.url, 'path'):
            path = request.url.path
            # Normalize path parameters
            if '/recommendations/' in path:
                return '/recommendations/{id}'
            elif '/users/' in path:
                return '/users/{id}'
            elif '/books/' in path:
                return '/books/{id}'
            return path
        return 'unknown'


def track_function_metrics(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator to track function execution metrics."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record success metrics
                if metric_name == 'recommendation':
                    metrics_collector.record_recommendation(
                        user_type=labels.get('user_type', 'unknown'),
                        rec_type=labels.get('rec_type', 'hybrid'),
                        duration=duration
                    )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                metrics_collector.record_error(
                    error_type=type(e).__name__,
                    severity='error'
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record success metrics based on metric_name
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                metrics_collector.record_error(
                    error_type=type(e).__name__,
                    severity='error'
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Global metrics collector instance
metrics_collector = MetricsCollector()


async def get_metrics() -> str:
    """Generate Prometheus metrics output."""
    return generate_latest(REGISTRY)


def get_correlation_id() -> str:
    """Get current request correlation ID."""
    return correlation_id.get('')
