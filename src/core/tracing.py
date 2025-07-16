"""
OpenTelemetry tracing implementation for distributed request tracing.
Provides comprehensive observability across service boundaries.
"""

import os
import time
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

from opentelemetry import trace, baggage, propagate
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.propagators.jaeger import JaegerPropagator
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter
)
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION

logger = logging.getLogger(__name__)


class TracingConfig:
    """Configuration for distributed tracing."""
    
    def __init__(self):
        self.service_name = os.getenv('SERVICE_NAME', 'goodbooks-recommender')
        self.service_version = os.getenv('SERVICE_VERSION', '1.0.0')
        self.jaeger_endpoint = os.getenv('JAEGER_ENDPOINT', 'http://jaeger:14268/api/traces')
        self.tracing_enabled = os.getenv('TRACING_ENABLED', 'true').lower() == 'true'
        self.sampling_rate = float(os.getenv('TRACING_SAMPLING_RATE', '1.0'))
        self.environment = os.getenv('ENVIRONMENT', 'development')


class DistributedTracing:
    """Centralized distributed tracing management."""
    
    def __init__(self, config: Optional[TracingConfig] = None):
        self.config = config or TracingConfig()
        self.tracer = None
        self._initialized = False
    
    def initialize(self):
        """Initialize OpenTelemetry tracing."""
        if self._initialized or not self.config.tracing_enabled:
            return
        
        try:
            # Create resource
            resource = Resource.create({
                SERVICE_NAME: self.config.service_name,
                SERVICE_VERSION: self.config.service_version,
                "environment": self.config.environment,
                "deployment.type": "container"
            })
            
            # Create tracer provider
            tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(tracer_provider)
            
            # Configure exporters
            self._setup_exporters(tracer_provider)
            
            # Configure propagators
            self._setup_propagators()
            
            # Get tracer
            self.tracer = trace.get_tracer(
                __name__,
                version=self.config.service_version
            )
            
            # Initialize instrumentations
            self._setup_instrumentations()
            
            self._initialized = True
            logger.info(
                "Distributed tracing initialized",
                extra={
                    "service_name": self.config.service_name,
                    "jaeger_endpoint": self.config.jaeger_endpoint,
                    "sampling_rate": self.config.sampling_rate
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize tracing: {e}")
            # Continue without tracing rather than failing
    
    def _setup_exporters(self, tracer_provider: TracerProvider):
        """Setup trace exporters."""
        try:
            # Jaeger exporter for production
            jaeger_exporter = JaegerExporter(
                endpoint=self.config.jaeger_endpoint,
                max_tag_value_length=1024,
                username=os.getenv('JAEGER_USERNAME'),
                password=os.getenv('JAEGER_PASSWORD')
            )
            
            span_processor = BatchSpanProcessor(
                jaeger_exporter,
                max_queue_size=2048,
                max_export_batch_size=512,
                export_timeout_millis=30000,
                schedule_delay_millis=1000
            )
            tracer_provider.add_span_processor(span_processor)
            
            # Console exporter for development
            if self.config.environment == 'development':
                console_exporter = ConsoleSpanExporter()
                console_processor = BatchSpanProcessor(console_exporter)
                tracer_provider.add_span_processor(console_processor)
                
        except Exception as e:
            logger.warning(f"Failed to setup Jaeger exporter: {e}")
            # Fallback to console exporter
            console_exporter = ConsoleSpanExporter()
            console_processor = BatchSpanProcessor(console_exporter)
            tracer_provider.add_span_processor(console_processor)
    
    def _setup_propagators(self):
        """Setup trace context propagators."""
        propagate.set_global_textmap(
            CompositePropagator([
                JaegerPropagator(),
                B3MultiFormat(),
                # TraceContextTextMapPropagator(),  # W3C Trace Context
            ])
        )
    
    def _setup_instrumentations(self):
        """Setup automatic instrumentation for common libraries."""
        try:
            # HTTP requests instrumentation
            RequestsInstrumentor().instrument()
            
            # Redis instrumentation
            RedisInstrumentor().instrument()
            
            # PostgreSQL instrumentation
            AsyncPGInstrumentor().instrument()
            
            # Logging instrumentation
            LoggingInstrumentor().instrument(set_logging_format=True)
            
            logger.info("Auto-instrumentation setup completed")
            
        except Exception as e:
            logger.warning(f"Some instrumentations failed: {e}")
    
    def instrument_fastapi(self, app):
        """Instrument FastAPI application."""
        if not self._initialized:
            return
        
        try:
            FastAPIInstrumentor.instrument_app(
                app,
                tracer_provider=trace.get_tracer_provider(),
                excluded_urls="health,metrics,docs,openapi.json"
            )
            logger.info("FastAPI instrumentation completed")
        except Exception as e:
            logger.error(f"Failed to instrument FastAPI: {e}")
    
    def create_span(self, 
                   name: str, 
                   attributes: Optional[Dict[str, Any]] = None,
                   kind: trace.SpanKind = trace.SpanKind.INTERNAL):
        """Create a new span."""
        if not self.tracer:
            return trace.NoOpSpan()
        
        span = self.tracer.start_span(name, kind=kind)
        
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        return span
    
    @contextmanager
    def trace_operation(self, 
                       operation_name: str,
                       attributes: Optional[Dict[str, Any]] = None,
                       kind: trace.SpanKind = trace.SpanKind.INTERNAL):
        """Context manager for tracing operations."""
        span = self.create_span(operation_name, attributes, kind)
        
        try:
            with trace.use_span(span):
                yield span
        except Exception as e:
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise
        finally:
            span.end()
    
    def add_span_attribute(self, key: str, value: Any):
        """Add attribute to current span."""
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            current_span.set_attribute(key, value)
    
    def add_span_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add event to current span."""
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            current_span.add_event(name, attributes or {})
    
    def set_baggage(self, key: str, value: str):
        """Set baggage item for cross-service propagation."""
        baggage.set_baggage(key, value)
    
    def get_baggage(self, key: str) -> Optional[str]:
        """Get baggage item."""
        return baggage.get_baggage(key)
    
    def get_trace_id(self) -> str:
        """Get current trace ID."""
        current_span = trace.get_current_span()
        if current_span and current_span.get_span_context().trace_id:
            return format(current_span.get_span_context().trace_id, '032x')
        return ""
    
    def get_span_id(self) -> str:
        """Get current span ID."""
        current_span = trace.get_current_span()
        if current_span and current_span.get_span_context().span_id:
            return format(current_span.get_span_context().span_id, '016x')
        return ""


# Global tracing instance
tracing = DistributedTracing()


def trace_function(operation_name: Optional[str] = None, 
                  attributes: Optional[Dict[str, Any]] = None):
    """Decorator for tracing function calls."""
    def decorator(func):
        import functools
        import asyncio
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracing.trace_operation(op_name, attributes) as span:
                # Add function parameters as attributes
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                result = await func(*args, **kwargs)
                return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracing.trace_operation(op_name, attributes) as span:
                # Add function parameters as attributes
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                result = func(*args, **kwargs)
                return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def trace_ml_operation(model_name: str, operation_type: str):
    """Decorator specifically for ML operations."""
    def decorator(func):
        import functools
        import asyncio
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            attributes = {
                "ml.model.name": model_name,
                "ml.operation.type": operation_type,
                "component": "ml_pipeline"
            }
            
            with tracing.trace_operation(f"ml.{operation_type}", attributes) as span:
                start_time = time.time()
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # Add result metrics
                    if hasattr(result, '__len__'):
                        span.set_attribute("ml.result.count", len(result))
                    
                    duration = time.time() - start_time
                    span.set_attribute("ml.operation.duration_ms", duration * 1000)
                    
                    return result
                    
                except Exception as e:
                    span.set_attribute("ml.operation.error", str(e))
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            attributes = {
                "ml.model.name": model_name,
                "ml.operation.type": operation_type,
                "component": "ml_pipeline"
            }
            
            with tracing.trace_operation(f"ml.{operation_type}", attributes) as span:
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Add result metrics
                    if hasattr(result, '__len__'):
                        span.set_attribute("ml.result.count", len(result))
                    
                    duration = time.time() - start_time
                    span.set_attribute("ml.operation.duration_ms", duration * 1000)
                    
                    return result
                    
                except Exception as e:
                    span.set_attribute("ml.operation.error", str(e))
                    raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator
