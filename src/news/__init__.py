"""
AI News Intelligence System
Integrates with existing GoodBooks infrastructure for news intelligence
"""

__version__ = "1.0.0"
__author__ = "GoodBooks AI Team"

from .ai.summarization import AISummarizationPipeline
from .core.intelligence_engine import NewsArticle, NewsIntelligenceEngine, NewsSource
from .personalization.recommender import HybridNewsRecommender

__all__ = [
    "NewsIntelligenceEngine",
    "NewsArticle",
    "NewsSource",
    "AISummarizationPipeline",
    "HybridNewsRecommender",
]
