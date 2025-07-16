"""
Custom exception hierarchy for the GoodBooks application.
Follows bookworm instructions for structured error handling.
"""
from typing import Any, Dict, Optional


class GoodBooksException(Exception):
    """Base exception for the GoodBooks application."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DataLoadError(GoodBooksException):
    """Raised when data loading fails."""
    pass


class ModelTrainingError(GoodBooksException):
    """Raised when model training fails."""
    pass


class RecommendationError(GoodBooksException):
    """Raised when recommendation generation fails."""
    pass


class CacheError(GoodBooksException):
    """Raised when cache operations fail."""
    pass


class ValidationError(GoodBooksException):
    """Raised when input validation fails."""
    pass


class AuthenticationError(GoodBooksException):
    """Raised when authentication fails."""
    pass


class RateLimitError(GoodBooksException):
    """Raised when rate limits are exceeded."""
    pass


class ConfigurationError(GoodBooksException):
    """Raised when configuration is invalid."""
    pass


class ExternalServiceError(GoodBooksException):
    """Raised when external service calls fail."""
    pass
