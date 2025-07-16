"""
False News Detection System - Core Models and Schemas
This module defines the foundational data structures used across all components.
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
import uuid


class AnalysisDepth(str, Enum):
    """Analysis depth levels for detection requests."""
    QUICK = "quick"              # Basic text analysis only
    STANDARD = "standard"        # All modules except deep media analysis
    DEEP = "deep"               # Full analysis including deep media verification
    COMPREHENSIVE = "comprehensive"  # All modules + orchestration refinement


class Verdict(str, Enum):
    """Possible verdicts for fake news detection."""
    AUTHENTIC = "authentic"      # Content appears to be genuine
    MISLEADING = "misleading"    # Contains some truth but misleading context
    FALSE = "false"             # Factually incorrect or fabricated
    UNCERTAIN = "uncertain"      # Insufficient evidence to determine
    SATIRE = "satire"           # Satirical/parody content


class AnalysisStatus(str, Enum):
    """Status of analysis request."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ContentType(str, Enum):
    """Types of content that can be analyzed."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    MIXED = "mixed"


class EvidenceType(str, Enum):
    """Types of evidence that can support or refute claims."""
    FACT_CHECK = "fact_check"
    SOURCE_VERIFICATION = "source_verification"
    TIMELINE_VERIFICATION = "timeline_verification"
    NETWORK_ANALYSIS = "network_analysis"
    MEDIA_FORENSICS = "media_forensics"
    LINGUISTIC_ANALYSIS = "linguistic_analysis"
    EXPERT_OPINION = "expert_opinion"


# Request Models
class DetectionRequest(BaseModel):
    """Request model for fake news detection."""
    
    # Content inputs
    text_content: Optional[str] = Field(None, max_length=50000, description="Text content to analyze")
    image_urls: Optional[List[str]] = Field(None, max_items=10, description="URLs of images to analyze")
    media_files: Optional[List[str]] = Field(None, max_items=5, description="Paths to media files")
    
    # Context information
    source_url: Optional[str] = Field(None, description="Original source URL")
    author_info: Optional[Dict[str, Any]] = Field(None, description="Author/publisher information")
    publication_date: Optional[datetime] = Field(None, description="Publication timestamp")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    
    # Analysis configuration
    analysis_depth: AnalysisDepth = Field(AnalysisDepth.STANDARD, description="Depth of analysis")
    require_explanation: bool = Field(True, description="Whether to generate explanations")
    priority: int = Field(5, ge=1, le=10, description="Request priority (1=highest, 10=lowest)")
    
    # User preferences
    language: Optional[str] = Field("en", description="Content language")
    custom_thresholds: Optional[Dict[str, float]] = Field(None, description="Custom confidence thresholds")
    
    @validator("text_content")
    def validate_text_content(cls, v):
        if v is not None and len(v.strip()) < 10:
            raise ValueError("Text content too short for meaningful analysis")
        return v
    
    @validator("image_urls")
    def validate_image_urls(cls, v):
        if v:
            for url in v:
                if not url.startswith(('http://', 'https://')):
                    raise ValueError(f"Invalid URL format: {url}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "text_content": "Breaking: Scientists discover new cure for aging...",
                "source_url": "https://example.com/article",
                "author_info": {"name": "John Doe", "credentials": "Medical Reporter"},
                "analysis_depth": "standard",
                "require_explanation": True,
                "priority": 5
            }
        }


# Evidence and Analysis Models
class Evidence(BaseModel):
    """Evidence supporting or refuting a claim."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: EvidenceType
    source: str = Field(..., description="Source of the evidence")
    content: str = Field(..., description="Evidence content or description")
    reliability_score: float = Field(..., ge=0.0, le=1.0, description="Reliability of the evidence")
    supporting: bool = Field(..., description="Whether evidence supports (True) or refutes (False) the claim")
    timestamp: Optional[datetime] = Field(None, description="When evidence was found")
    source_credibility: Optional[float] = Field(None, ge=0.0, le=1.0, description="Credibility of evidence source")
    verification_method: Optional[str] = Field(None, description="How evidence was verified")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "fact_check",
                "source": "Snopes",
                "content": "Similar claim was rated as false in 2023",
                "reliability_score": 0.95,
                "supporting": False,
                "source_credibility": 0.92
            }
        }


class ConfidenceInterval(BaseModel):
    """Confidence interval for uncertainty quantification."""
    
    lower_bound: float = Field(..., ge=0.0, le=1.0)
    upper_bound: float = Field(..., ge=0.0, le=1.0)
    confidence_level: float = Field(0.95, ge=0.0, le=1.0)
    
    @validator("upper_bound")
    def validate_bounds(cls, v, values):
        if "lower_bound" in values and v < values["lower_bound"]:
            raise ValueError("Upper bound must be >= lower bound")
        return v


class Explanation(BaseModel):
    """Human-readable explanation of the analysis."""
    
    summary: str = Field(..., description="Brief summary of the analysis")
    detailed_analysis: str = Field(..., description="Detailed explanation of findings")
    key_factors: List[str] = Field(..., description="Key factors influencing the verdict")
    methodology: List[str] = Field(..., description="Analysis methods used")
    limitations: List[str] = Field(..., description="Limitations of the analysis")
    confidence_reasoning: str = Field(..., description="Explanation of confidence level")
    
    class Config:
        schema_extra = {
            "example": {
                "summary": "Content contains misleading statistics about medical research",
                "detailed_analysis": "The article claims a 95% cure rate, but source studies show only 12% improvement...",
                "key_factors": ["Statistical manipulation", "Unverified sources", "Sensational language"],
                "methodology": ["Fact verification", "Source credibility analysis", "Statistical validation"],
                "limitations": ["Limited access to original data", "Recent publication - peer review pending"]
            }
        }


class ModelPrediction(BaseModel):
    """Prediction from an individual ML model."""
    
    model_name: str
    verdict: Verdict
    confidence: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: int
    model_version: Optional[str] = None
    features_used: Optional[List[str]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "model_name": "GPT-4-FakeNews-v1",
                "verdict": "misleading",
                "confidence": 0.78,
                "processing_time_ms": 1200,
                "model_version": "1.2.3"
            }
        }


# Response Models
class DetectionResponse(BaseModel):
    """Complete response for fake news detection."""
    
    # Request metadata
    request_id: str = Field(..., description="Unique request identifier")
    status: AnalysisStatus = Field(..., description="Current analysis status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Main verdict and scores
    verdict: Verdict = Field(..., description="Final detection verdict")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in verdict")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score for harmful misinformation")
    
    # Multi-dimensional analysis scores
    content_authenticity: float = Field(..., ge=0.0, le=1.0, description="Content authenticity score")
    source_credibility: float = Field(..., ge=0.0, le=1.0, description="Source credibility score")
    network_anomaly_score: float = Field(..., ge=0.0, le=1.0, description="Network propagation anomaly score")
    media_authenticity: float = Field(..., ge=0.0, le=1.0, description="Media authenticity score")
    temporal_consistency: float = Field(..., ge=0.0, le=1.0, description="Temporal consistency score")
    
    # Evidence and explanations
    evidence: List[Evidence] = Field(default_factory=list, description="Supporting evidence")
    explanation: Optional[Explanation] = Field(None, description="Detailed explanation")
    supporting_facts: List[str] = Field(default_factory=list, description="Facts supporting authenticity")
    contradicting_facts: List[str] = Field(default_factory=list, description="Facts contradicting claims")
    
    # Model predictions
    model_predictions: List[ModelPrediction] = Field(default_factory=list, description="Individual model predictions")
    ensemble_weights: Optional[Dict[str, float]] = Field(None, description="Model ensemble weights")
    
    # Analysis metadata
    analysis_duration_ms: int = Field(..., description="Total analysis time in milliseconds")
    models_used: List[str] = Field(..., description="List of models used in analysis")
    confidence_intervals: Dict[str, ConfidenceInterval] = Field(default_factory=dict, description="Confidence intervals")
    
    # Real-time update fields
    progress: Optional[float] = Field(None, ge=0.0, le=1.0, description="Analysis progress (0.0 to 1.0)")
    current_stage: Optional[str] = Field(None, description="Current analysis stage")
    
    # Quality metrics
    data_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Input data quality score")
    analysis_reliability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Analysis reliability score")
    
    class Config:
        schema_extra = {
            "example": {
                "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "status": "completed",
                "verdict": "misleading",
                "confidence_score": 0.78,
                "risk_score": 0.65,
                "content_authenticity": 0.45,
                "source_credibility": 0.82,
                "network_anomaly_score": 0.23,
                "media_authenticity": 0.91,
                "temporal_consistency": 0.67,
                "analysis_duration_ms": 2500,
                "models_used": ["GPT-4", "BERT-FakeNews", "XGBoost-Ensemble"],
                "progress": 1.0,
                "data_quality_score": 0.89
            }
        }


# Batch Processing Models
class BatchDetectionRequest(BaseModel):
    """Request for batch processing of multiple items."""
    
    items: List[DetectionRequest] = Field(..., max_items=100, description="Items to analyze")
    batch_name: Optional[str] = Field(None, description="Optional batch identifier")
    callback_url: Optional[str] = Field(None, description="Webhook URL for completion notification")
    priority: int = Field(5, ge=1, le=10, description="Batch priority")
    
    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {"text_content": "Article 1 content..."},
                    {"text_content": "Article 2 content..."}
                ],
                "batch_name": "daily_news_batch_2024_01_15",
                "callback_url": "https://example.com/webhook/batch-complete"
            }
        }


class BatchDetectionResponse(BaseModel):
    """Response for batch processing."""
    
    batch_id: str = Field(..., description="Unique batch identifier")
    status: AnalysisStatus = Field(..., description="Batch processing status")
    total_items: int = Field(..., description="Total number of items in batch")
    completed_items: int = Field(0, description="Number of completed items")
    failed_items: int = Field(0, description="Number of failed items")
    results: List[DetectionResponse] = Field(default_factory=list, description="Individual analysis results")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    
    @property
    def progress_percentage(self) -> float:
        """Calculate batch progress percentage."""
        return (self.completed_items + self.failed_items) / self.total_items * 100 if self.total_items > 0 else 0


# Administrative Models
class SystemStats(BaseModel):
    """System statistics and health metrics."""
    
    total_requests: int = Field(..., description="Total requests processed")
    requests_last_24h: int = Field(..., description="Requests in last 24 hours")
    average_response_time: float = Field(..., description="Average response time in seconds")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Success rate")
    active_models: List[str] = Field(..., description="Currently active models")
    system_load: Dict[str, float] = Field(..., description="System resource usage")
    cache_hit_rate: float = Field(..., ge=0.0, le=1.0, description="Cache hit rate")
    
    class Config:
        schema_extra = {
            "example": {
                "total_requests": 150000,
                "requests_last_24h": 2500,
                "average_response_time": 1.8,
                "success_rate": 0.987,
                "active_models": ["GPT-4", "BERT", "XGBoost"],
                "system_load": {"cpu": 0.65, "memory": 0.78, "disk": 0.45},
                "cache_hit_rate": 0.92
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response for load balancers."""
    
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="System version")
    components: Dict[str, str] = Field(..., description="Component health status")
    uptime_seconds: int = Field(..., description="System uptime in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "components": {
                    "database": "healthy",
                    "redis": "healthy",
                    "ml_models": "healthy",
                    "external_apis": "degraded"
                },
                "uptime_seconds": 86400
            }
        }


# Error Models
class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    error_code: str = Field(..., description="Machine-readable error code")
    error_message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "error_code": "INVALID_INPUT",
                "error_message": "Text content is required for analysis",
                "details": {"field": "text_content", "constraint": "min_length"},
                "request_id": "req_12345"
            }
        }


# Validation Models
class ValidationResult(BaseModel):
    """Result of input validation."""
    
    is_valid: bool = Field(..., description="Whether input is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    content_hash: str = Field(..., description="Hash of validated content")
    content_type: ContentType = Field(..., description="Detected content type")
    estimated_processing_time: Optional[int] = Field(None, description="Estimated processing time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": ["Large image file may slow processing"],
                "content_hash": "abc123def456",
                "content_type": "mixed",
                "estimated_processing_time": 15
            }
        }


# WebSocket Models
class WebSocketMessage(BaseModel):
    """WebSocket message format for real-time updates."""
    
    message_type: str = Field(..., description="Type of message")
    request_id: str = Field(..., description="Associated request ID")
    data: Dict[str, Any] = Field(..., description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "message_type": "progress_update",
                "request_id": "req_12345",
                "data": {
                    "progress": 0.6,
                    "current_stage": "network_analysis",
                    "estimated_remaining": 30
                }
            }
        }
