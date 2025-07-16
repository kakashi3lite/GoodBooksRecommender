"""
Enhanced structured logging with correlation IDs and ELK Stack integration.
Follows production-grade logging standards for observability.
"""

import os
import json
import logging
import logging.config
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, List
from pathlib import Path
import uuid

from pythonjsonlogger import jsonlogger

from src.core.monitoring import get_correlation_id


class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def filter(self, record):
        record.correlation_id = get_correlation_id() or str(uuid.uuid4())
        record.timestamp = datetime.utcnow().isoformat()
        record.environment = os.getenv('ENVIRONMENT', 'development')
        return True


class ElasticSearchFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for Elasticsearch/ELK Stack compatibility."""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Ensure required fields are present
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat()
        
        if not log_record.get('level'):
            log_record['level'] = record.levelname
        
        if not log_record.get('logger'):
            log_record['logger'] = record.name
        
        # Add service information
        log_record['service'] = 'goodbooks-recommender'
        log_record['version'] = '1.0.0'
        log_record['environment'] = getattr(record, 'environment', 'development')
        
        # Add correlation ID
        log_record['correlation_id'] = getattr(record, 'correlation_id', '')
        
        # Add thread and process info
        log_record['thread_id'] = record.thread
        log_record['process_id'] = record.process
        
        # Add location information
        log_record['file'] = record.filename
        log_record['line'] = record.lineno
        log_record['function'] = record.funcName
        
        # Handle exceptions
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }


class LoggingConfig:
    """Centralized logging configuration."""
    
    def __init__(self):
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.log_format = os.getenv('LOG_FORMAT', 'json')  # json or text
        self.log_dir = Path(os.getenv('LOG_DIR', 'logs'))
        self.max_file_size = int(os.getenv('LOG_MAX_FILE_SIZE', 100 * 1024 * 1024))  # 100MB
        self.backup_count = int(os.getenv('LOG_BACKUP_COUNT', 5))
        self.enable_console = os.getenv('LOG_ENABLE_CONSOLE', 'true').lower() == 'true'
        self.enable_file = os.getenv('LOG_ENABLE_FILE', 'true').lower() == 'true'
        self.elasticsearch_enabled = os.getenv('ELASTICSEARCH_ENABLED', 'false').lower() == 'true'
        self.elasticsearch_host = os.getenv('ELASTICSEARCH_HOST', 'elasticsearch:9200')
        self.elasticsearch_index = os.getenv('ELASTICSEARCH_INDEX', 'goodbooks-logs')
        
        # Create log directory
        self.log_dir.mkdir(exist_ok=True)
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration dictionary."""
        
        # Formatters
        formatters = {
            'json': {
                '()': ElasticSearchFormatter,
                'format': '%(timestamp)s %(level)s %(logger)s %(message)s'
            },
            'detailed': {
                'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] [%(correlation_id)s] %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s: %(message)s'
            }
        }
        
        # Filters
        filters = {
            'correlation': {
                '()': CorrelationFilter,
            }
        }
        
        # Handlers
        handlers = {}
        
        # Console handler
        if self.enable_console:
            handlers['console'] = {
                'class': 'logging.StreamHandler',
                'level': self.log_level,
                'formatter': 'json' if self.log_format == 'json' else 'detailed',
                'filters': ['correlation'],
                'stream': 'ext://sys.stdout'
            }
        
        # File handlers
        if self.enable_file:
            # Application logs
            handlers['file_app'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'json',
                'filters': ['correlation'],
                'filename': str(self.log_dir / 'app.log'),
                'maxBytes': self.max_file_size,
                'backupCount': self.backup_count,
                'encoding': 'utf-8'
            }
            
            # Error logs
            handlers['file_error'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'json',
                'filters': ['correlation'],
                'filename': str(self.log_dir / 'error.log'),
                'maxBytes': self.max_file_size,
                'backupCount': self.backup_count,
                'encoding': 'utf-8'
            }
            
            # Access logs
            handlers['file_access'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'json',
                'filters': ['correlation'],
                'filename': str(self.log_dir / 'access.log'),
                'maxBytes': self.max_file_size,
                'backupCount': self.backup_count,
                'encoding': 'utf-8'
            }
            
            # Performance logs
            handlers['file_performance'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'json',
                'filters': ['correlation'],
                'filename': str(self.log_dir / 'performance.log'),
                'maxBytes': self.max_file_size,
                'backupCount': self.backup_count,
                'encoding': 'utf-8'
            }
        
        # Elasticsearch handler (if enabled)
        if self.elasticsearch_enabled:
            try:
                handlers['elasticsearch'] = {
                    'class': 'cmreslogging.handlers.CMRESHandler',
                    'level': 'INFO',
                    'formatter': 'json',
                    'filters': ['correlation'],
                    'hosts': [{'host': self.elasticsearch_host.split(':')[0], 
                              'port': int(self.elasticsearch_host.split(':')[1])}],
                    'index_name': self.elasticsearch_index,
                    'es_doc_type': 'log'
                }
            except ImportError:
                # cmreslogging not available, skip Elasticsearch handler
                pass
        
        # Loggers
        loggers = {
            'src': {
                'level': self.log_level,
                'handlers': list(handlers.keys()),
                'propagate': False
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': ['file_access'] if self.enable_file else ['console'],
                'propagate': False
            },
            'uvicorn.error': {
                'level': 'INFO',
                'handlers': ['file_error'] if self.enable_file else ['console'],
                'propagate': False
            },
            'sqlalchemy.engine': {
                'level': 'WARNING',
                'handlers': list(handlers.keys()),
                'propagate': False
            }
        }
        
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': formatters,
            'filters': filters,
            'handlers': handlers,
            'loggers': loggers,
            'root': {
                'level': self.log_level,
                'handlers': list(handlers.keys())
            }
        }


class StructuredLogger:
    """Production-ready structured logger with correlation IDs."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log with additional context."""
        extra = {
            'correlation_id': get_correlation_id(),
            'component': self.name,
            **kwargs
        }
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        extra = {
            'correlation_id': get_correlation_id(),
            'component': self.name,
            **kwargs
        }
        self.logger.exception(message, extra=extra)
    
    def performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics."""
        extra = {
            'correlation_id': get_correlation_id(),
            'component': self.name,
            'operation': operation,
            'duration_ms': duration * 1000,
            'performance_log': True,
            **kwargs
        }
        
        performance_logger = logging.getLogger('performance')
        performance_logger.info(f"Performance: {operation}", extra=extra)
    
    def audit(self, action: str, user_id: Optional[str] = None, **kwargs):
        """Log audit events."""
        extra = {
            'correlation_id': get_correlation_id(),
            'component': self.name,
            'action': action,
            'user_id': user_id,
            'audit_log': True,
            **kwargs
        }
        
        audit_logger = logging.getLogger('audit')
        audit_logger.info(f"Audit: {action}", extra=extra)
    
    def security(self, event: str, severity: str = 'medium', **kwargs):
        """Log security events."""
        extra = {
            'correlation_id': get_correlation_id(),
            'component': self.name,
            'security_event': event,
            'severity': severity,
            'security_log': True,
            **kwargs
        }
        
        security_logger = logging.getLogger('security')
        security_logger.warning(f"Security: {event}", extra=extra)


def setup_logging():
    """Setup application logging configuration."""
    config = LoggingConfig()
    logging_config = config.get_logging_config()
    
    try:
        logging.config.dictConfig(logging_config)
        
        # Test logging setup
        logger = StructuredLogger(__name__)
        logger.info("Logging system initialized", 
                   log_level=config.log_level,
                   log_format=config.log_format,
                   file_logging=config.enable_file,
                   elasticsearch_enabled=config.elasticsearch_enabled)
        
    except Exception as e:
        # Fallback to basic logging if configuration fails
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to setup structured logging: {e}")
        logger.info("Falling back to basic logging configuration")


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


# Log retention and cleanup utilities
class LogRetentionManager:
    """Manage log file retention and cleanup."""
    
    def __init__(self, log_dir: Path, retention_days: int = 30):
        self.log_dir = log_dir
        self.retention_days = retention_days
    
    def cleanup_old_logs(self):
        """Remove log files older than retention period."""
        import time
        from datetime import timedelta
        
        cutoff_time = time.time() - (self.retention_days * 24 * 60 * 60)
        
        try:
            for log_file in self.log_dir.glob('*.log*'):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    logger = get_logger(__name__)
                    logger.info(f"Removed old log file: {log_file}")
        
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Error during log cleanup: {e}")
    
    def compress_old_logs(self):
        """Compress old log files to save space."""
        import gzip
        import shutil
        
        try:
            for log_file in self.log_dir.glob('*.log.[0-9]*'):
                if not log_file.name.endswith('.gz'):
                    compressed_file = log_file.with_suffix(log_file.suffix + '.gz')
                    
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    log_file.unlink()
                    
                    logger = get_logger(__name__)
                    logger.info(f"Compressed log file: {log_file} -> {compressed_file}")
        
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Error during log compression: {e}")


# Initialize logging on module import
setup_logging()
