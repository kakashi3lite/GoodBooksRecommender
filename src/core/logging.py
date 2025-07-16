"""
Structured logging system following bookworm instructions.
Provides JSON-formatted logging with proper error handling.
"""
import logging
import sys
import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import traceback
from pythonjsonlogger import jsonlogger

from src.core.settings import settings


class StructuredLogger:
    """
    Structured logger that outputs JSON-formatted logs for production monitoring.
    Follows the bookworm instructions for comprehensive logging.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup logging handlers based on environment."""
        self.logger.setLevel(getattr(logging, settings.logging.level))
        
        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = self._get_formatter()
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for errors
        if not settings.is_testing:
            error_handler = logging.FileHandler(
                settings.logs_dir / "errors.log",
                encoding="utf-8"
            )
            error_formatter = self._get_formatter(include_traceback=True)
            error_handler.setFormatter(error_formatter)
            error_handler.setLevel(logging.ERROR)
            self.logger.addHandler(error_handler)
            
            # General application log
            app_handler = logging.FileHandler(
                settings.logs_dir / "app.log",
                encoding="utf-8"
            )
            app_handler.setFormatter(console_formatter)
            self.logger.addHandler(app_handler)        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _get_formatter(self, include_traceback: bool = False):
        """Get appropriate formatter based on configuration."""
        if settings.monitoring.log_format.lower() == "json":
            format_string = "%(asctime)s %(name)s %(levelname)s %(message)s"
            if include_traceback:
                format_string += " %(pathname)s %(lineno)d %(funcName)s"
            return jsonlogger.JsonFormatter(format_string)
        else:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            return logging.Formatter(format_string)
    
    def _create_log_data(self, **kwargs) -> Dict[str, Any]:
        """Create structured log data."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "logger": self.name,
            "environment": settings.environment,
        }
        
        # Add any additional context
        log_data.update(kwargs)        
        return log_data
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data."""
        extra = self._create_log_data(**kwargs)
        self.logger.debug(message, extra=extra)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data."""
        extra = self._create_log_data(**kwargs)
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data."""
        extra = self._create_log_data(**kwargs)
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message with structured data and optional exception info."""
        extra = self._create_log_data(**kwargs)
        
        if exc_info:
            extra["traceback"] = traceback.format_exc()
        
        self.logger.error(message, extra=extra, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log critical message with structured data."""
        extra = self._create_log_data(**kwargs)
        
        if exc_info:
            extra["traceback"] = traceback.format_exc()
        
        self.logger.critical(message, extra=extra, exc_info=exc_info)
    
    def log_request(self, method: str, url: str, status_code: int, 
                   duration: float, **kwargs):
        """Log HTTP request with standardized format."""
        self.info(
            "HTTP request",
            request_method=method,
            request_url=url,
            status_code=status_code,
            duration_ms=round(duration * 1000, 2),
            **kwargs
        )
    
    def log_recommendation_request(self, user_id: Optional[int], 
                                 book_title: Optional[str], 
                                 n_recommendations: int,
                                 duration: float,
                                 cache_hit: bool = False,
                                 **kwargs):
        """Log recommendation request with domain-specific context."""
        self.info(
            "Recommendation request",
            user_id=user_id,
            book_title=book_title,
            n_recommendations=n_recommendations,
            duration_ms=round(duration * 1000, 2),
            cache_hit=cache_hit,
            **kwargs
        )
    
    def log_model_performance(self, model_name: str, metrics: Dict[str, float], **kwargs):
        """Log model performance metrics."""
        self.info(
            "Model performance",
            model_name=model_name,
            metrics=metrics,
            **kwargs
        )
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any]):
        """Log error with full context for debugging."""
        self.error(
            f"Error occurred: {str(error)}",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context,
            exc_info=True
        )


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


def setup_logging():
    """Setup application-wide logging configuration."""
    # Create logs directory if it doesn't exist
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup root logger to catch any unhandled logs
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.logging.level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add a single handler to prevent duplicate logs
    if settings.logging.console_enabled:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)


# Setup root logger to catch any unhandled logs
def setup_root_logger():
    """Setup root logger for the application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.logging.level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add a single handler to prevent duplicate logs
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


# Initialize root logger
setup_root_logger()
