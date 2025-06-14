import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge
from fastapi import Request, Response
from src.config import Config

# Set up logging
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'goodbooks_request_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'goodbooks_request_latency_seconds',
    'Request latency in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'goodbooks_active_requests',
    'Number of active requests',
    ['method', 'endpoint']
)

RECOMMENDATION_COUNT = Counter(
    'goodbooks_recommendations_total',
    'Total number of recommendations generated',
    ['type']  # content-based, collaborative, or hybrid
)

CACHE_HITS = Counter(
    'goodbooks_cache_hits_total',
    'Total number of cache hits',
    ['cache_type']  # recommendations, model, etc.
)

CACHE_MISSES = Counter(
    'goodbooks_cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

MODEL_PREDICTION_TIME = Histogram(
    'goodbooks_model_prediction_seconds',
    'Time taken for model predictions',
    ['model_type']  # content-based, collaborative, or hybrid
)

class MetricsLogger:
    def __init__(self):
        self.config = Config()
    
    def log_request_metrics(self, request: Request, response: Response, duration: float):
        """Log request-related metrics."""
        try:
            # Update Prometheus metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            # Log request details
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'duration': f"{duration:.3f}s",
                'client_ip': request.client.host,
                'user_agent': request.headers.get('user-agent')
            }
            
            logger.info(f"Request metrics: {log_data}")
            
        except Exception as e:
            logger.error(f"Error logging request metrics: {str(e)}")
    
    def log_recommendation_metrics(self, recommendation_type: str, duration: float, cache_hit: bool):
        """Log recommendation-related metrics."""
        try:
            # Update Prometheus metrics
            RECOMMENDATION_COUNT.labels(type=recommendation_type).inc()
            
            MODEL_PREDICTION_TIME.labels(model_type=recommendation_type).observe(duration)
            
            if cache_hit:
                CACHE_HITS.labels(cache_type='recommendations').inc()
            else:
                CACHE_MISSES.labels(cache_type='recommendations').inc()
            
            # Log recommendation details
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'type': recommendation_type,
                'duration': f"{duration:.3f}s",
                'cache_hit': cache_hit
            }
            
            logger.info(f"Recommendation metrics: {log_data}")
            
        except Exception as e:
            logger.error(f"Error logging recommendation metrics: {str(e)}")
    
    def log_error(self, error: Exception, request: Optional[Request] = None):
        """Log error details."""
        try:
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'error_type': type(error).__name__,
                'error_message': str(error)
            }
            
            if request:
                log_data.update({
                    'method': request.method,
                    'path': request.url.path,
                    'client_ip': request.client.host
                })
            
            logger.error(f"Error occurred: {log_data}", exc_info=True)
            
        except Exception as e:
            logger.error(f"Error logging error details: {str(e)}")

# Create metrics middleware
metrics_logger = MetricsLogger()

def track_metrics(func):
    """Decorator to track metrics for API endpoints."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        start_time = time.time()
        
        try:
            # Increment active requests
            if request:
                ACTIVE_REQUESTS.labels(
                    method=request.method,
                    endpoint=request.url.path
                ).inc()
            
            # Execute the endpoint
            response = await func(*args, **kwargs)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log metrics
            if request:
                metrics_logger.log_request_metrics(
                    request=request,
                    response=response,
                    duration=duration
                )
            
            return response
            
        except Exception as e:
            # Log error
            metrics_logger.log_error(error=e, request=request)
            raise
            
        finally:
            # Decrement active requests
            if request:
                ACTIVE_REQUESTS.labels(
                    method=request.method,
                    endpoint=request.url.path
                ).dec()
    
    return wrapper