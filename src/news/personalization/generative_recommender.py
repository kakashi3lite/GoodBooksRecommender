"""
Generative News Recommendation (GNR) System
Advanced narrative coalescence for coherent story weaving
COT: Traditional rec engines miss narrative flow—GNR merges articles into stories
"""

import asyncio
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import aiohttp
import numpy as np

from src.core.logging import StructuredLogger
from src.news.core.intelligence_engine import NewsArticle, NewsSource
from src.news.ai.scorerag_summarization import ScoreRAGProcessor, EvidenceCluster

logger = StructuredLogger(__name__)


@dataclass
class StoryCluster:
    """Related articles forming a coherent narrative"""
    
    cluster_id: str
    title: str
    narrative_summary: str
    related_articles: List[NewsArticle]
    timeline: List[datetime]
    key_entities: Set[str]
    geographic_scope: List[str]
    story_arc: str  # "breaking", "developing", "conclusion", "ongoing"
    coherence_score: float  # 0-1, narrative coherence
    importance_score: float  # 0-1, story importance
    reading_time_minutes: int


@dataclass
class NarrativeRecommendation:
    """GNR narrative recommendation with story flow"""
    
    story_cluster: StoryCluster
    recommendation_reason: str
    user_interest_match: float
    narrative_flow_score: float
    depth_level: str  # "headline", "summary", "deep_dive"
    next_story_suggestions: List[str]
    related_perspectives: List[Dict[str, Any]]


class GenerativeNewsRecommender:
    """
    COT: GNR merges multiple articles into coherent stories
    
    Research Integration: Narrative coalescence methodology
    - Identify related articles across time and sources
    - Generate coherent story arcs with temporal flow
    - Create "In-Depth Stories" that weave related content
    - Present unified narratives instead of isolated articles
    """

    def __init__(self, scorerag_processor: Optional[ScoreRAGProcessor] = None):
        self.scorerag_processor = scorerag_processor or ScoreRAGProcessor()
        self.session = None
        
        # GNR parameters
        self.story_similarity_threshold = 0.7
        self.max_story_articles = 8
        self.narrative_lookback_days = 7
        self.coherence_min_threshold = 0.6
        
        # Entity extraction patterns (simplified NER)
        self.entity_patterns = {
            'person': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            'organization': r'\b[A-Z][A-Z\s]+\b',
            'location': r'\b[A-Z][a-z]+(?:,\s*[A-Z][a-z]+)*\b'
        }

    async def __aenter__(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(limit=15, ttl_dns_cache=300)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=20)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def generate_narrative_recommendations(
        self,
        user_id: str,
        candidate_articles: List[NewsArticle],
        user_interests: Optional[Dict[str, float]] = None,
        max_stories: int = 5
    ) -> List[NarrativeRecommendation]:
        """
        COT: Generate narrative recommendations with story coalescence
        
        Process:
        1. Cluster articles into coherent stories
        2. Generate narrative summaries for each cluster
        3. Score user interest alignment
        4. Create deep-dive story recommendations
        """
        try:
            # Stage 1: Story Clustering
            story_clusters = await self._cluster_articles_into_stories(candidate_articles)
            
            # Stage 2: Narrative Generation
            enriched_clusters = await self._generate_narrative_summaries(story_clusters)
            
            # Stage 3: User Interest Matching
            scored_clusters = await self._score_user_interest_alignment(
                enriched_clusters, user_interests or {}
            )
            
            # Stage 4: Recommendation Creation
            recommendations = await self._create_narrative_recommendations(
                scored_clusters, user_id
            )

            return recommendations[:max_stories]

        except Exception as e:
            logger.error("GNR narrative generation failed", error=str(e))
            raise

    async def _cluster_articles_into_stories(
        self, 
        articles: List[NewsArticle]
    ) -> List[StoryCluster]:
        """
        COT: Group related articles into coherent story clusters
        Uses entity overlap, temporal proximity, and semantic similarity
        """
        if not articles:
            return []

        clusters = []
        used_articles = set()
        
        for i, seed_article in enumerate(articles):
            if seed_article.id in used_articles:
                continue
                
            # Find related articles
            related_articles = [seed_article]
            cluster_entities = self._extract_entities(seed_article.content)
            
            for j, candidate in enumerate(articles):
                if (candidate.id != seed_article.id and 
                    candidate.id not in used_articles):
                    
                    # Check entity overlap
                    candidate_entities = self._extract_entities(candidate.content)
                    entity_overlap = len(cluster_entities & candidate_entities) / max(
                        len(cluster_entities | candidate_entities), 1
                    )
                    
                    # Check temporal proximity (within 7 days)
                    time_diff = abs((candidate.published_at - seed_article.published_at).days)
                    temporal_score = 1.0 if time_diff <= 7 else 0.0
                    
                    # Combined similarity score
                    similarity_score = entity_overlap * 0.7 + temporal_score * 0.3
                    
                    if similarity_score >= self.story_similarity_threshold:
                        related_articles.append(candidate)
                        cluster_entities.update(candidate_entities)
                        
                        if len(related_articles) >= self.max_story_articles:
                            break
            
            # Mark articles as used
            for article in related_articles:
                used_articles.add(article.id)
            
            # Create story cluster
            if len(related_articles) >= 2:  # Minimum for a story
                cluster = StoryCluster(
                    cluster_id=f"story_{i}",
                    title=self._generate_cluster_title(related_articles),
                    narrative_summary="",  # Will be generated later
                    related_articles=sorted(related_articles, key=lambda x: x.published_at),
                    timeline=[article.published_at for article in related_articles],
                    key_entities=cluster_entities,
                    geographic_scope=self._extract_locations(related_articles),
                    story_arc=self._determine_story_arc(related_articles),
                    coherence_score=0.0,  # Will be calculated
                    importance_score=0.0,  # Will be calculated
                    reading_time_minutes=sum(a.reading_time_minutes for a in related_articles)
                )
                clusters.append(cluster)

        return clusters

    async def _generate_narrative_summaries(
        self, 
        clusters: List[StoryCluster]
    ) -> List[StoryCluster]:
        """
        COT: Generate coherent narrative summaries that weave articles together
        Creates unified story flow instead of isolated article summaries
        """
        for cluster in clusters:
            # Create narrative prompt
            narrative_prompt = self._create_narrative_prompt(cluster)
            
            # Generate narrative using LLM (simplified - would use Claude API)
            narrative_summary = await self._generate_llm_narrative(narrative_prompt)
            
            # Update cluster
            cluster.narrative_summary = narrative_summary
            cluster.coherence_score = self._calculate_coherence_score(cluster)
            cluster.importance_score = self._calculate_importance_score(cluster)

        return clusters

    def _create_narrative_prompt(self, cluster: StoryCluster) -> str:
        """
        COT: Create few-shot prompt for narrative generation
        Uses temporal flow and entity relationships
        """
        articles_summary = "\n".join([
            f"[{article.published_at.strftime('%Y-%m-%d')}] {article.title}: {article.summary or article.content[:200]}..."
            for article in cluster.related_articles
        ])
        
        return f"""
Create a coherent narrative summary that weaves these related news articles into a unified story.

Story Arc: {cluster.story_arc}
Key Entities: {', '.join(list(cluster.key_entities)[:5])}
Timeline: {cluster.timeline[0].strftime('%Y-%m-%d')} to {cluster.timeline[-1].strftime('%Y-%m-%d')}

Articles:
{articles_summary}

Instructions:
1. Create a flowing narrative that connects these events chronologically
2. Highlight the relationship between different developments
3. Explain the overall significance and implications
4. Keep it concise but comprehensive (150-200 words)
5. Use clear, engaging language suitable for news readers

Narrative Summary:
"""

    async def _generate_llm_narrative(self, prompt: str) -> str:
        """
        COT: Generate narrative using LLM
        In production, this would call Claude API
        For now, create a structured summary
        """
        # Simplified narrative generation
        # In production: call Claude API with narrative prompt
        
        return "This developing story involves multiple related events that have unfolded over recent days. The narrative connects key developments through a coherent timeline, showing how initial events led to subsequent outcomes. The story demonstrates the interconnected nature of recent news developments and their broader implications for stakeholders involved."

    async def _score_user_interest_alignment(
        self,
        clusters: List[StoryCluster],
        user_interests: Dict[str, float]
    ) -> List[StoryCluster]:
        """
        COT: Score how well each story cluster aligns with user interests
        Consider entity matches, topic preferences, and reading history
        """
        for cluster in clusters:
            interest_score = 0.0
            
            # Entity-based interest matching
            for entity in cluster.key_entities:
                if entity.lower() in user_interests:
                    interest_score += user_interests[entity.lower()]
            
            # Topic-based matching (simplified)
            cluster_topics = set()
            for article in cluster.related_articles:
                cluster_topics.update(article.topics)
            
            for topic in cluster_topics:
                if topic.lower() in user_interests:
                    interest_score += user_interests[topic.lower()]
            
            # Normalize by number of factors
            total_factors = len(cluster.key_entities) + len(cluster_topics)
            cluster.importance_score = min(1.0, interest_score / max(total_factors, 1))

        return sorted(clusters, key=lambda c: c.importance_score, reverse=True)

    async def _create_narrative_recommendations(
        self,
        clusters: List[StoryCluster],
        user_id: str
    ) -> List[NarrativeRecommendation]:
        """
        COT: Create final narrative recommendations with explanations
        Include depth levels and related perspectives
        """
        recommendations = []
        
        for cluster in clusters:
            if cluster.coherence_score >= self.coherence_min_threshold:
                
                # Determine depth level based on article count and reading time
                if cluster.reading_time_minutes <= 5:
                    depth_level = "headline"
                elif cluster.reading_time_minutes <= 15:
                    depth_level = "summary"
                else:
                    depth_level = "deep_dive"
                
                # Generate recommendation reason
                reason = self._generate_recommendation_reason(cluster)
                
                # Find related perspectives (opposing viewpoints)
                related_perspectives = self._find_related_perspectives(cluster)
                
                recommendation = NarrativeRecommendation(
                    story_cluster=cluster,
                    recommendation_reason=reason,
                    user_interest_match=cluster.importance_score,
                    narrative_flow_score=cluster.coherence_score,
                    depth_level=depth_level,
                    next_story_suggestions=self._suggest_next_stories(cluster),
                    related_perspectives=related_perspectives
                )
                
                recommendations.append(recommendation)

        return recommendations

    def _extract_entities(self, text: str) -> Set[str]:
        """Simple entity extraction using regex patterns"""
        entities = set()
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text)
            entities.update(matches)
        
        return entities

    def _extract_locations(self, articles: List[NewsArticle]) -> List[str]:
        """Extract geographic scope from articles"""
        locations = set()
        
        for article in articles:
            # Simple location extraction
            location_matches = re.findall(r'\b[A-Z][a-z]+(?:,\s*[A-Z][a-z]+)*\b', article.content)
            locations.update(location_matches[:3])  # Top 3 per article
        
        return list(locations)[:5]  # Top 5 overall

    def _determine_story_arc(self, articles: List[NewsArticle]) -> str:
        """Determine the story arc based on content analysis"""
        if not articles:
            return "unknown"
        
        # Simple heuristic based on keywords and timeline
        latest_article = max(articles, key=lambda x: x.published_at)
        timeline_span = (max(a.published_at for a in articles) - 
                        min(a.published_at for a in articles)).days
        
        if timeline_span == 0:
            return "breaking"
        elif timeline_span <= 2:
            return "developing"
        elif timeline_span <= 7:
            return "ongoing"
        else:
            return "conclusion"

    def _generate_cluster_title(self, articles: List[NewsArticle]) -> str:
        """Generate a title for the story cluster"""
        if not articles:
            return "Unknown Story"
        
        # Use the most recent article's title as base
        latest_article = max(articles, key=lambda x: x.published_at)
        return f"Story: {latest_article.title}"

    def _calculate_coherence_score(self, cluster: StoryCluster) -> float:
        """Calculate narrative coherence score"""
        if len(cluster.related_articles) <= 1:
            return 1.0
        
        # Simple coherence based on entity overlap and temporal flow
        entity_density = len(cluster.key_entities) / len(cluster.related_articles)
        temporal_coherence = 1.0 if len(cluster.timeline) == len(cluster.related_articles) else 0.5
        
        return min(1.0, entity_density * 0.6 + temporal_coherence * 0.4)

    def _calculate_importance_score(self, cluster: StoryCluster) -> float:
        """Calculate story importance score"""
        # Based on number of articles, credibility, and recency
        article_count_score = min(1.0, len(cluster.related_articles) / 5.0)
        credibility_score = np.mean([a.credibility_score for a in cluster.related_articles])
        
        # Recency score (more recent = more important)
        latest_article = max(cluster.related_articles, key=lambda x: x.published_at)
        hours_ago = (datetime.now() - latest_article.published_at).total_seconds() / 3600
        recency_score = max(0.0, 1.0 - hours_ago / 48.0)  # Decay over 48 hours
        
        return (article_count_score * 0.3 + credibility_score * 0.4 + recency_score * 0.3)

    def _generate_recommendation_reason(self, cluster: StoryCluster) -> str:
        """Generate explanation for why this story is recommended"""
        reasons = []
        
        if cluster.story_arc == "breaking":
            reasons.append("Breaking news story")
        elif cluster.story_arc == "developing":
            reasons.append("Developing story with new updates")
        
        if cluster.importance_score > 0.8:
            reasons.append("High importance and user relevance")
        
        if len(cluster.related_articles) >= 5:
            reasons.append("Comprehensive coverage from multiple sources")
        
        return " • ".join(reasons) if reasons else "Related to your interests"

    def _find_related_perspectives(self, cluster: StoryCluster) -> List[Dict[str, Any]]:
        """Find related perspectives or opposing viewpoints"""
        # Simplified implementation
        perspectives = []
        
        # Group by source bias if available
        source_groups = {}
        for article in cluster.related_articles:
            bias = article.bias_rating or "neutral"
            if bias not in source_groups:
                source_groups[bias] = []
            source_groups[bias].append(article)
        
        for bias, articles in source_groups.items():
            if len(articles) >= 2:
                perspectives.append({
                    "perspective": bias,
                    "article_count": len(articles),
                    "sample_title": articles[0].title
                })
        
        return perspectives

    def _suggest_next_stories(self, cluster: StoryCluster) -> List[str]:
        """Suggest related story clusters user might be interested in"""
        # Simplified suggestion based on entities
        suggestions = []
        
        for entity in list(cluster.key_entities)[:3]:
            suggestions.append(f"More stories about {entity}")
        
        return suggestions


# Few-shot prompt template for GNR
GNR_NARRATIVE_PROMPT_TEMPLATE = """
You are an expert news editor specializing in narrative coherence and story flow.

TASK: Weave multiple related news articles into a single, coherent narrative story.

ARTICLES TO MERGE:
{articles_with_timeline}

STORY CONTEXT:
- Story Arc: {story_arc}
- Key Entities: {key_entities}
- Geographic Scope: {locations}
- Timeline: {start_date} to {end_date}

INSTRUCTIONS:
1. Create a flowing narrative that shows how events connect chronologically
2. Highlight cause-and-effect relationships between developments  
3. Explain the broader significance and implications
4. Use engaging, clear language suitable for news readers
5. Maintain journalistic objectivity while showing narrative flow
6. Include key entities and their roles in the story

OUTPUT FORMAT:
Narrative Title: [Compelling title that captures the story arc]

Story Summary: [150-200 word narrative that weaves events together]

Key Developments:
• [Development 1 with date]
• [Development 2 with date]  
• [Development 3 with date]

What's Next: [1-2 sentences about likely future developments]

EXAMPLE:
Title: "Tech Giant's Privacy Battle Escalates Through Regulatory Challenges"

Story: "What began as a routine privacy audit has evolved into a major regulatory confrontation affecting millions of users. The story unfolded when regulators first raised concerns about data handling practices, leading to increased scrutiny and eventual formal investigations. As the company pushed back with legal challenges, the conflict expanded to include congressional hearings and international regulatory coordination. The developing situation now threatens to reshape privacy legislation industry-wide..."
"""
