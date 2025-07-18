"""
AI-First Newsletter System - Hyper-Personalization Engine
Production-grade newsletter platform with 10× engagement optimization.
Follows Bookworm AI coding standards.
"""

from .core.personalization_engine import PersonalizationEngine
from .core.content_curator import AIContentCurator
from .core.send_time_optimizer import SendTimeOptimizer
from .templates.adaptive_templates import AdaptiveTemplateEngine
from .campaigns.campaign_manager import CampaignManager
from .analytics.engagement_analytics import EngagementAnalytics
from .agents.hyper_personalization_agent import HyperPersonalizationAgent

__version__ = "1.0.0"
__author__ = "Bookworm AI"
__description__ = "AI-First Newsletter Platform with Hyper-Personalization"

__all__ = [
    "PersonalizationEngine",
    "AIContentCurator", 
    "SendTimeOptimizer",
    "AdaptiveTemplateEngine",
    "CampaignManager",
    "EngagementAnalytics",
    "HyperPersonalizationAgent"
]
