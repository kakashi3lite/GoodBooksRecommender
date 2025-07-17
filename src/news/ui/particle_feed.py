"""
Particle-Style Multi-Perspective News Feed
Story clustering with viewpoint organization and perspective toggling
COT: Users need depth and diversity—organize stories by viewpoint like Particle app
"""

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import aiohttp
import numpy as np

from src.core.logging import StructuredLogger
from src.news.core.intelligence_engine import NewsArticle
from src.news.personalization.generative_recommender import StoryCluster, GenerativeNewsRecommender

logger = StructuredLogger(__name__)


class PerspectiveType(Enum):
    """Different perspective types for viewpoint analysis"""
    MAINSTREAM = "mainstream"
    ALTERNATIVE = "alternative"
    CONSERVATIVE = "conservative"
    LIBERAL = "liberal"
    INTERNATIONAL = "international"
    LOCAL = "local"
    EXPERT = "expert"
    PUBLIC = "public"


@dataclass
class ViewpointCluster:
    """Cluster of articles representing a specific viewpoint"""
    
    cluster_id: str
    perspective_type: PerspectiveType
    viewpoint_summary: str
    key_arguments: List[str]
    supporting_articles: List[NewsArticle]
    source_bias_rating: str  # "left", "center", "right", "mixed"
    confidence_score: float  # How confident we are in this viewpoint classification
    evidence_strength: float  # Strength of evidence supporting this viewpoint
    article_count: int
    geographic_origin: List[str]


@dataclass
class StoryPerspectiveGroup:
    """Multi-perspective story group following Particle app model"""
    
    story_id: str
    story_title: str
    story_summary: str
    main_timeline: List[datetime]
    total_articles: int
    
    # Particle-style organization
    side_a_viewpoint: ViewpointCluster  # Primary perspective
    side_b_viewpoint: ViewpointCluster  # Contrasting perspective
    additional_viewpoints: List[ViewpointCluster]  # Other perspectives
    
    # NLP-generated comparisons
    key_differences: List[str]
    shared_facts: List[str]
    disputed_claims: List[str]
    
    # User interaction
    user_can_toggle: bool
    default_perspective: str
    reading_complexity: str  # "simple", "moderate", "complex"


@dataclass
class PerspectiveFeedCard:
    """Feed card with perspective toggle capability"""
    
    story_group: StoryPerspectiveGroup
    current_perspective: PerspectiveType
    quick_toggle_available: bool
    bullet_comparison: List[str]  # Quick side-by-side bullets
    estimated_read_time: int
    perspective_balance_score: float  # How well-balanced the coverage is


class ParticleStyleFeedManager:
    """
    COT: Emulate Particle's multi-perspective feed organization
    
    Research Integration: Particle app methodology
    - Group multi-source stories into clusters
    - Organize by contrasting viewpoints (Side A / Side B)
    - Generate NLP bullet comparisons
    - Enable perspective toggling
    - Present unified story with diverse angles
    """

    def __init__(self, gnr_recommender: Optional[GenerativeNewsRecommender] = None):
        self.gnr_recommender = gnr_recommender or GenerativeNewsRecommender()
        self.session = None
        
        # Particle-style parameters
        self.min_articles_for_perspective = 2
        self.max_perspectives_per_story = 4
        self.similarity_threshold = 0.65
        self.bias_detection_confidence = 0.7
        
        # Bias detection patterns (simplified)
        self.bias_indicators = {
            "liberal": ["progressive", "inclusive", "social justice", "climate action", "equality"],
            "conservative": ["traditional", "security", "law and order", "fiscal responsibility", "heritage"],
            "mainstream": ["officials said", "according to", "reported", "sources confirm"],
            "alternative": ["insider claims", "leaked documents", "exclusive investigation", "whistleblower"]
        }

    async def __aenter__(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(limit=15, ttl_dns_cache=300)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=25)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def create_perspective_feed(
        self,
        articles: List[NewsArticle],
        user_preferences: Optional[Dict[str, Any]] = None,
        max_story_groups: int = 10
    ) -> List[PerspectiveFeedCard]:
        """
        COT: Create Particle-style perspective feed with story clustering
        
        Process:
        1. Cluster articles into stories
        2. Identify different perspectives within each story
        3. Organize into Side A / Side B viewpoints
        4. Generate NLP bullet comparisons
        5. Create toggleable feed cards
        """
        try:
            logger.info("Creating Particle-style perspective feed", article_count=len(articles))
            
            # Stage 1: Story Clustering
            story_clusters = await self._cluster_stories_for_perspectives(articles)
            
            # Stage 2: Perspective Analysis
            perspective_groups = await self._analyze_story_perspectives(story_clusters)
            
            # Stage 3: Viewpoint Organization
            organized_groups = await self._organize_into_sides(perspective_groups)
            
            # Stage 4: Generate Comparisons
            comparison_groups = await self._generate_perspective_comparisons(organized_groups)
            
            # Stage 5: Create Feed Cards
            feed_cards = await self._create_perspective_feed_cards(
                comparison_groups, user_preferences
            )

            logger.info(f"Created {len(feed_cards)} perspective feed cards")
            return feed_cards[:max_story_groups]

        except Exception as e:
            logger.error("Perspective feed creation failed", error=str(e))
            raise

    async def _cluster_stories_for_perspectives(
        self, 
        articles: List[NewsArticle]
    ) -> List[StoryCluster]:
        """
        COT: Cluster articles into stories suitable for perspective analysis
        Focus on controversial or multi-faceted topics
        """
        # Use existing GNR clustering but filter for perspective-worthy stories
        async with self.gnr_recommender as gnr:
            all_clusters = await gnr._cluster_articles_into_stories(articles)
        
        # Filter clusters that have potential for multiple perspectives
        perspective_worthy = []
        
        for cluster in all_clusters:
            if len(cluster.related_articles) >= self.min_articles_for_perspective:
                # Check for perspective diversity indicators
                source_diversity = len(set(a.source for a in cluster.related_articles))
                bias_diversity = len(set(a.bias_rating for a in cluster.related_articles if a.bias_rating))
                
                if source_diversity >= 2 or bias_diversity >= 2:
                    perspective_worthy.append(cluster)
        
        return perspective_worthy

    async def _analyze_story_perspectives(
        self, 
        story_clusters: List[StoryCluster]
    ) -> List[StoryPerspectiveGroup]:
        """
        COT: Analyze each story cluster for different perspectives
        Identify contrasting viewpoints and organize by perspective type
        """
        perspective_groups = []
        
        for cluster in story_clusters:
            # Identify viewpoints within the cluster
            viewpoint_clusters = await self._identify_viewpoints_in_cluster(cluster)
            
            if len(viewpoint_clusters) >= 2:  # Need at least 2 perspectives
                # Create perspective group
                group = StoryPerspectiveGroup(
                    story_id=cluster.cluster_id,
                    story_title=cluster.title,
                    story_summary=cluster.narrative_summary,
                    main_timeline=cluster.timeline,
                    total_articles=len(cluster.related_articles),
                    side_a_viewpoint=viewpoint_clusters[0],  # Will be assigned later
                    side_b_viewpoint=viewpoint_clusters[1],  # Will be assigned later
                    additional_viewpoints=viewpoint_clusters[2:],
                    key_differences=[],  # Will be generated
                    shared_facts=[],     # Will be generated
                    disputed_claims=[],  # Will be generated
                    user_can_toggle=True,
                    default_perspective="mainstream",
                    reading_complexity=self._assess_reading_complexity(cluster)
                )
                
                perspective_groups.append(group)
        
        return perspective_groups

    async def _identify_viewpoints_in_cluster(
        self, 
        cluster: StoryCluster
    ) -> List[ViewpointCluster]:
        """
        COT: Identify distinct viewpoints within a story cluster
        Group articles by perspective using bias detection and content analysis
        """
        viewpoints = []
        used_articles = set()
        
        # Group articles by detected bias/perspective
        bias_groups = {}
        for article in cluster.related_articles:
            if article.id in used_articles:
                continue
            
            # Detect perspective type
            detected_perspective = self._detect_article_perspective(article)
            
            if detected_perspective not in bias_groups:
                bias_groups[detected_perspective] = []
            
            bias_groups[detected_perspective].append(article)
            used_articles.add(article.id)
        
        # Create viewpoint clusters
        for perspective_type, articles in bias_groups.items():
            if len(articles) >= 1:  # At least 1 article per viewpoint
                viewpoint = ViewpointCluster(
                    cluster_id=f"{cluster.cluster_id}_{perspective_type.value}",
                    perspective_type=perspective_type,
                    viewpoint_summary=self._generate_viewpoint_summary(articles),
                    key_arguments=self._extract_key_arguments(articles),
                    supporting_articles=articles,
                    source_bias_rating=self._assess_source_bias(articles),
                    confidence_score=self._calculate_perspective_confidence(articles, perspective_type),
                    evidence_strength=self._assess_evidence_strength(articles),
                    article_count=len(articles),
                    geographic_origin=self._extract_geographic_origin(articles)
                )
                viewpoints.append(viewpoint)
        
        return sorted(viewpoints, key=lambda v: v.confidence_score, reverse=True)

    def _detect_article_perspective(self, article: NewsArticle) -> PerspectiveType:
        """
        COT: Detect perspective type using content analysis
        Simple keyword-based detection (can be enhanced with ML)
        """
        content_lower = f"{article.title} {article.content}".lower()
        
        # Score each perspective type
        perspective_scores = {}
        
        for bias_type, indicators in self.bias_indicators.items():
            score = sum(1 for indicator in indicators if indicator in content_lower)
            if bias_type == "liberal":
                perspective_scores[PerspectiveType.LIBERAL] = score
            elif bias_type == "conservative":
                perspective_scores[PerspectiveType.CONSERVATIVE] = score
            elif bias_type == "mainstream":
                perspective_scores[PerspectiveType.MAINSTREAM] = score
            elif bias_type == "alternative":
                perspective_scores[PerspectiveType.ALTERNATIVE] = score
        
        # Check for international vs local indicators
        international_indicators = ["international", "global", "worldwide", "UN", "NATO"]
        local_indicators = ["local", "city", "county", "community", "neighborhood"]
        
        international_score = sum(1 for ind in international_indicators if ind in content_lower)
        local_score = sum(1 for ind in local_indicators if ind in content_lower)
        
        perspective_scores[PerspectiveType.INTERNATIONAL] = international_score
        perspective_scores[PerspectiveType.LOCAL] = local_score
        
        # Return highest scoring perspective
        if perspective_scores:
            best_perspective = max(perspective_scores.items(), key=lambda x: x[1])
            if best_perspective[1] > 0:
                return best_perspective[0]
        
        # Default to mainstream if no clear indicators
        return PerspectiveType.MAINSTREAM

    async def _organize_into_sides(
        self, 
        perspective_groups: List[StoryPerspectiveGroup]
    ) -> List[StoryPerspectiveGroup]:
        """
        COT: Organize perspectives into Particle-style Side A / Side B
        Choose most contrasting viewpoints for primary sides
        """
        for group in perspective_groups:
            viewpoints = [group.side_a_viewpoint, group.side_b_viewpoint] + group.additional_viewpoints
            
            if len(viewpoints) >= 2:
                # Find most contrasting pair
                contrast_pairs = []
                
                for i in range(len(viewpoints)):
                    for j in range(i + 1, len(viewpoints)):
                        contrast_score = self._calculate_perspective_contrast(
                            viewpoints[i], viewpoints[j]
                        )
                        contrast_pairs.append((viewpoints[i], viewpoints[j], contrast_score))
                
                # Select highest contrast pair
                if contrast_pairs:
                    best_pair = max(contrast_pairs, key=lambda x: x[2])
                    group.side_a_viewpoint = best_pair[0]
                    group.side_b_viewpoint = best_pair[1]
                    
                    # Remaining viewpoints as additional
                    group.additional_viewpoints = [
                        v for v in viewpoints 
                        if v != best_pair[0] and v != best_pair[1]
                    ]
        
        return perspective_groups

    def _calculate_perspective_contrast(
        self, 
        viewpoint1: ViewpointCluster, 
        viewpoint2: ViewpointCluster
    ) -> float:
        """
        COT: Calculate contrast score between two viewpoints
        Higher score = more contrasting perspectives
        """
        # Perspective type contrast
        type_contrast = {
            (PerspectiveType.LIBERAL, PerspectiveType.CONSERVATIVE): 1.0,
            (PerspectiveType.MAINSTREAM, PerspectiveType.ALTERNATIVE): 0.8,
            (PerspectiveType.INTERNATIONAL, PerspectiveType.LOCAL): 0.6,
            (PerspectiveType.EXPERT, PerspectiveType.PUBLIC): 0.7
        }
        
        # Check both directions
        pair = (viewpoint1.perspective_type, viewpoint2.perspective_type)
        reverse_pair = (viewpoint2.perspective_type, viewpoint1.perspective_type)
        
        contrast_score = type_contrast.get(pair, type_contrast.get(reverse_pair, 0.3))
        
        # Bias rating contrast
        bias_contrast = 0.0
        if (viewpoint1.source_bias_rating == "left" and viewpoint2.source_bias_rating == "right") or \
           (viewpoint1.source_bias_rating == "right" and viewpoint2.source_bias_rating == "left"):
            bias_contrast = 0.5
        
        return min(1.0, contrast_score + bias_contrast)

    async def _generate_perspective_comparisons(
        self, 
        organized_groups: List[StoryPerspectiveGroup]
    ) -> List[StoryPerspectiveGroup]:
        """
        COT: Generate NLP bullet comparisons between perspectives
        Create side-by-side comparison points
        """
        for group in organized_groups:
            # Generate comparisons between Side A and Side B
            comparisons = await self._create_side_by_side_comparison(
                group.side_a_viewpoint, group.side_b_viewpoint
            )
            
            group.key_differences = comparisons["differences"]
            group.shared_facts = comparisons["shared_facts"]
            group.disputed_claims = comparisons["disputed_claims"]
        
        return organized_groups

    async def _create_side_by_side_comparison(
        self, 
        side_a: ViewpointCluster, 
        side_b: ViewpointCluster
    ) -> Dict[str, List[str]]:
        """
        COT: Create detailed side-by-side comparison
        Identify differences, shared facts, and disputed claims
        """
        # Extract key points from each side
        side_a_points = set(side_a.key_arguments)
        side_b_points = set(side_b.key_arguments)
        
        # Find shared and disputed points
        shared_facts = []
        differences = []
        disputed_claims = []
        
        # Simple comparison logic (can be enhanced with NLP)
        for point_a in side_a_points:
            # Look for similar or opposing points in side B
            similar_found = False
            for point_b in side_b_points:
                if self._are_points_similar(point_a, point_b):
                    shared_facts.append(f"Both sides: {point_a}")
                    similar_found = True
                elif self._are_points_opposing(point_a, point_b):
                    disputed_claims.append(f"Side A: {point_a} | Side B: {point_b}")
                    similar_found = True
            
            if not similar_found:
                differences.append(f"Side A unique: {point_a}")
        
        # Add unique points from side B
        for point_b in side_b_points:
            if not any(self._are_points_similar(point_b, point_a) for point_a in side_a_points):
                differences.append(f"Side B unique: {point_b}")
        
        return {
            "shared_facts": shared_facts[:3],      # Top 3 shared facts
            "differences": differences[:4],        # Top 4 differences  
            "disputed_claims": disputed_claims[:2] # Top 2 disputed claims
        }

    async def _create_perspective_feed_cards(
        self,
        comparison_groups: List[StoryPerspectiveGroup],
        user_preferences: Optional[Dict[str, Any]]
    ) -> List[PerspectiveFeedCard]:
        """
        COT: Create final feed cards with perspective toggle capability
        Include quick bullet comparisons and user interaction features
        """
        feed_cards = []
        
        for group in comparison_groups:
            # Determine default perspective based on user preferences
            default_perspective = self._determine_default_perspective(group, user_preferences)
            
            # Create bullet comparison for quick view
            bullet_comparison = self._create_bullet_comparison(group)
            
            # Calculate balance score
            balance_score = self._calculate_perspective_balance(group)
            
            feed_card = PerspectiveFeedCard(
                story_group=group,
                current_perspective=default_perspective,
                quick_toggle_available=len(group.additional_viewpoints) > 0,
                bullet_comparison=bullet_comparison,
                estimated_read_time=sum(a.reading_time_minutes for a in group.side_a_viewpoint.supporting_articles),
                perspective_balance_score=balance_score
            )
            
            feed_cards.append(feed_card)
        
        return sorted(feed_cards, key=lambda c: c.perspective_balance_score, reverse=True)

    def _generate_viewpoint_summary(self, articles: List[NewsArticle]) -> str:
        """Generate summary for a specific viewpoint"""
        if not articles:
            return "No articles available"
        
        # Simple summary from first article
        return articles[0].summary or articles[0].content[:200] + "..."

    def _extract_key_arguments(self, articles: List[NewsArticle]) -> List[str]:
        """Extract key arguments from articles representing a viewpoint"""
        arguments = []
        
        for article in articles[:3]:  # Top 3 articles
            # Simple argument extraction
            sentences = article.content.split('.')
            for sentence in sentences:
                sentence = sentence.strip()
                if (len(sentence) > 30 and 
                    any(keyword in sentence.lower() for keyword in 
                        ['argues', 'claims', 'believes', 'maintains', 'asserts'])):
                    arguments.append(sentence)
        
        return arguments[:3]  # Top 3 arguments

    def _assess_source_bias(self, articles: List[NewsArticle]) -> str:
        """Assess overall bias of sources"""
        bias_ratings = [a.bias_rating for a in articles if a.bias_rating]
        
        if not bias_ratings:
            return "unknown"
        
        # Simple majority voting
        left_count = bias_ratings.count("left")
        right_count = bias_ratings.count("right")
        center_count = bias_ratings.count("center")
        
        if left_count > right_count and left_count > center_count:
            return "left"
        elif right_count > left_count and right_count > center_count:
            return "right"
        else:
            return "center"

    def _calculate_perspective_confidence(
        self, 
        articles: List[NewsArticle], 
        perspective_type: PerspectiveType
    ) -> float:
        """Calculate confidence in perspective classification"""
        # Simple confidence based on article count and credibility
        article_count_score = min(1.0, len(articles) / 3.0)
        credibility_score = np.mean([a.credibility_score for a in articles])
        
        return (article_count_score * 0.4 + credibility_score * 0.6)

    def _assess_evidence_strength(self, articles: List[NewsArticle]) -> float:
        """Assess strength of evidence in articles"""
        # Simple evidence indicators
        evidence_keywords = ["study", "research", "data", "statistics", "expert", "analysis"]
        
        total_evidence = 0
        for article in articles:
            content_lower = article.content.lower()
            evidence_count = sum(1 for keyword in evidence_keywords if keyword in content_lower)
            total_evidence += evidence_count
        
        return min(1.0, total_evidence / (len(articles) * 3))  # Normalize

    def _extract_geographic_origin(self, articles: List[NewsArticle]) -> List[str]:
        """Extract geographic origins from articles"""
        locations = set()
        
        for article in articles:
            # Simple location extraction from source or content
            if hasattr(article, 'location'):
                locations.add(article.location)
            
            # Extract from content (simplified)
            location_indicators = ["in", "from", "at"]
            for indicator in location_indicators:
                # This would be enhanced with proper NER
                pass
        
        return list(locations)[:3]

    def _assess_reading_complexity(self, cluster: StoryCluster) -> str:
        """Assess reading complexity of story cluster"""
        total_words = sum(len(a.content.split()) for a in cluster.related_articles)
        avg_words = total_words / len(cluster.related_articles)
        
        if avg_words < 300:
            return "simple"
        elif avg_words < 600:
            return "moderate"
        else:
            return "complex"

    def _are_points_similar(self, point1: str, point2: str) -> bool:
        """Check if two points are similar"""
        # Simple keyword overlap
        words1 = set(point1.lower().split())
        words2 = set(point2.lower().split())
        overlap = len(words1 & words2) / max(len(words1 | words2), 1)
        return overlap > 0.5

    def _are_points_opposing(self, point1: str, point2: str) -> bool:
        """Check if two points are opposing"""
        # Simple opposition detection
        opposing_pairs = [
            ("support", "oppose"), ("favor", "against"), ("increase", "decrease"),
            ("positive", "negative"), ("benefit", "harm"), ("success", "failure")
        ]
        
        point1_lower = point1.lower()
        point2_lower = point2.lower()
        
        for word1, word2 in opposing_pairs:
            if (word1 in point1_lower and word2 in point2_lower) or \
               (word2 in point1_lower and word1 in point2_lower):
                return True
        
        return False

    def _determine_default_perspective(
        self, 
        group: StoryPerspectiveGroup, 
        user_preferences: Optional[Dict[str, Any]]
    ) -> PerspectiveType:
        """Determine default perspective based on user preferences"""
        if not user_preferences:
            return group.side_a_viewpoint.perspective_type
        
        # Check user's preferred perspective
        preferred_bias = user_preferences.get("preferred_bias", "center")
        
        if preferred_bias == "left" and group.side_a_viewpoint.source_bias_rating == "left":
            return group.side_a_viewpoint.perspective_type
        elif preferred_bias == "right" and group.side_b_viewpoint.source_bias_rating == "right":
            return group.side_b_viewpoint.perspective_type
        
        # Default to highest confidence perspective
        if group.side_a_viewpoint.confidence_score >= group.side_b_viewpoint.confidence_score:
            return group.side_a_viewpoint.perspective_type
        else:
            return group.side_b_viewpoint.perspective_type

    def _create_bullet_comparison(self, group: StoryPerspectiveGroup) -> List[str]:
        """Create quick bullet comparison for feed card"""
        bullets = []
        
        # Add key difference
        if group.key_differences:
            bullets.append(f"📍 {group.key_differences[0]}")
        
        # Add shared fact
        if group.shared_facts:
            bullets.append(f"🤝 {group.shared_facts[0]}")
        
        # Add disputed claim
        if group.disputed_claims:
            bullets.append(f"⚖️ {group.disputed_claims[0]}")
        
        return bullets

    def _calculate_perspective_balance(self, group: StoryPerspectiveGroup) -> float:
        """Calculate how well-balanced the perspective coverage is"""
        # Balance based on article count, credibility, and evidence strength
        side_a_strength = (group.side_a_viewpoint.article_count * 
                          group.side_a_viewpoint.confidence_score * 
                          group.side_a_viewpoint.evidence_strength)
        
        side_b_strength = (group.side_b_viewpoint.article_count * 
                          group.side_b_viewpoint.confidence_score * 
                          group.side_b_viewpoint.evidence_strength)
        
        # Balance score (closer to 0.5 = more balanced)
        if side_a_strength + side_b_strength == 0:
            return 0.0
        
        balance_ratio = min(side_a_strength, side_b_strength) / max(side_a_strength, side_b_strength)
        return balance_ratio


# Particle-Style UI Component Integration
PARTICLE_FEED_CARD_TEMPLATE = """
<div class="particle-story-card" data-story-id="{story_id}">
    <div class="story-header">
        <h3 class="story-title">{story_title}</h3>
        <div class="perspective-toggle">
            <button class="side-toggle active" data-side="a">Side A</button>
            <button class="side-toggle" data-side="b">Side B</button>
            {additional_perspectives_buttons}
        </div>
    </div>
    
    <div class="story-content">
        <div class="perspective-content active" data-perspective="a">
            <div class="perspective-label">{side_a_label}</div>
            <p class="perspective-summary">{side_a_summary}</p>
            <div class="key-arguments">
                {side_a_arguments}
            </div>
            <div class="article-count">{side_a_article_count} articles</div>
        </div>
        
        <div class="perspective-content" data-perspective="b">
            <div class="perspective-label">{side_b_label}</div>
            <p class="perspective-summary">{side_b_summary}</p>
            <div class="key-arguments">
                {side_b_arguments}
            </div>
            <div class="article-count">{side_b_article_count} articles</div>
        </div>
    </div>
    
    <div class="quick-comparison">
        <h4>Quick Compare</h4>
        <div class="comparison-bullets">
            {bullet_comparison_items}
        </div>
    </div>
    
    <div class="story-metadata">
        <span class="reading-time">{estimated_read_time} min read</span>
        <span class="balance-score">Balance: {balance_score:.0%}</span>
        <span class="article-total">{total_articles} sources</span>
    </div>
</div>
"""
