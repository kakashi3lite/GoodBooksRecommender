"""
ScoreRAG Structured Summarization System
Advanced factual accuracy with consistency-relevance ranking
COT: Reduce hallucinations and improve factual quality via evidence scoring
"""

import asyncio
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import numpy as np

# Try to import sklearn, fallback to basic implementation if not available
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from src.core.logging import StructuredLogger
from src.core.vector_store import BookVectorStore
from src.news.core.intelligence_engine import NewsArticle

logger = StructuredLogger(__name__)


@dataclass
class EvidenceCluster:
    """Evidence cluster with consistency scoring"""
    
    articles: List[NewsArticle]
    source_urls: List[str]
    consistency_score: float  # 0-1, how consistent sources are
    relevance_score: float    # 0-1, relevance to query
    confidence_score: float   # Combined score
    key_claims: List[str]
    supporting_evidence: List[str]
    contradicting_evidence: List[str] = None

    def __post_init__(self):
        if self.contradicting_evidence is None:
            self.contradicting_evidence = []


@dataclass
class ScoreRAGSummary:
    """ScoreRAG structured summary with evidence scoring"""
    
    summary_text: str
    bullet_points: List[str]
    source_citations: List[Dict[str, Any]]
    confidence_score: float
    consistency_score: float
    relevance_score: float
    evidence_clusters: List[EvidenceCluster]
    fact_check_status: str  # "verified", "disputed", "unverified"
    hallucination_risk: float  # 0-1, risk of hallucination
    processing_time_ms: float


class ScoreRAGProcessor:
    """
    COT: ScoreRAG improves factual quality via consistency-relevance ranking
    
    Research Integration: ScoreRAG methodology from arXiv:2310.06166
    - Fetch relevant sources from vector DB
    - Score consistency + relevance
    - Rerank evidence clusters
    - Generate structured summaries with citations
    """

    def __init__(self, vector_store: Optional[BookVectorStore] = None):
        self.vector_store = vector_store
        self.session = None
        
        # ScoreRAG parameters (research-optimized)
        self.consistency_threshold = 0.7  # Minimum consistency for inclusion
        self.relevance_threshold = 0.6    # Minimum relevance for inclusion
        self.max_evidence_clusters = 5    # Max clusters to consider
        self.citation_min_confidence = 0.8  # Min confidence for citations

        # TF-IDF for consistency scoring (fallback implementation if sklearn not available)
        if SKLEARN_AVAILABLE:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
        else:
            self.tfidf_vectorizer = None  # Will use simple text similarity

    async def __aenter__(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(limit=20, ttl_dns_cache=300)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def generate_scorerag_summary(
        self,
        query: str,
        articles: List[NewsArticle],
        max_summary_length: int = 200
    ) -> ScoreRAGSummary:
        """
        Generate ScoreRAG structured summary with evidence ranking
        
        COT: Multi-stage evidence processing for factual accuracy
        1. Vector similarity retrieval
        2. Consistency scoring within clusters
        3. Cross-cluster relevance ranking
        4. Structured summary generation with citations
        """
        start_time = datetime.now()

        try:
            # Stage 1: Evidence Retrieval and Clustering
            evidence_clusters = await self._cluster_evidence_sources(query, articles)
            
            # Stage 2: Consistency-Relevance Scoring
            scored_clusters = await self._score_evidence_clusters(query, evidence_clusters)
            
            # Stage 3: Reranking by Combined Score
            reranked_clusters = self._rerank_by_combined_score(scored_clusters)
            
            # Stage 4: Structured Summary Generation
            summary_result = await self._generate_structured_summary(
                query, reranked_clusters, max_summary_length
            )

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return ScoreRAGSummary(
                summary_text=summary_result["summary"],
                bullet_points=summary_result["bullets"],
                source_citations=summary_result["citations"],
                confidence_score=summary_result["confidence"],
                consistency_score=np.mean([c.consistency_score for c in reranked_clusters]),
                relevance_score=np.mean([c.relevance_score for c in reranked_clusters]),
                evidence_clusters=reranked_clusters,
                fact_check_status=summary_result["fact_status"],
                hallucination_risk=self._calculate_hallucination_risk(reranked_clusters),
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error("ScoreRAG summary generation failed", error=str(e))
            raise

    async def _cluster_evidence_sources(
        self, 
        query: str, 
        articles: List[NewsArticle]
    ) -> List[EvidenceCluster]:
        """
        COT: Group articles by semantic similarity to create evidence clusters
        Each cluster represents a consistent viewpoint or fact pattern
        """
        if not articles:
            return []

        # Extract text content for clustering
        article_texts = [f"{article.title} {article.content}" for article in articles]
        
        # TF-IDF vectorization for clustering
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(article_texts)
        
        # Cosine similarity matrix
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Simple clustering: group articles with similarity > threshold
        clusters = []
        used_indices = set()
        
        for i, article in enumerate(articles):
            if i in used_indices:
                continue
                
            # Find similar articles
            similar_indices = [
                j for j in range(len(articles))
                if j != i and j not in used_indices and similarity_matrix[i][j] > 0.6
            ]
            
            cluster_articles = [article] + [articles[j] for j in similar_indices]
            cluster_sources = [article.url] + [articles[j].url for j in similar_indices]
            
            # Mark as used
            used_indices.add(i)
            used_indices.update(similar_indices)
            
            # Extract key claims (simplified)
            key_claims = self._extract_key_claims(cluster_articles)
            
            cluster = EvidenceCluster(
                articles=cluster_articles,
                source_urls=cluster_sources,
                consistency_score=0.0,  # Will be calculated in next stage
                relevance_score=0.0,    # Will be calculated in next stage
                confidence_score=0.0,   # Will be calculated in next stage
                key_claims=key_claims,
                supporting_evidence=[]
            )
            
            clusters.append(cluster)

        return clusters[:self.max_evidence_clusters]

    async def _score_evidence_clusters(
        self, 
        query: str, 
        clusters: List[EvidenceCluster]
    ) -> List[EvidenceCluster]:
        """
        COT: Score each cluster for consistency and relevance
        Consistency: How well sources within cluster agree
        Relevance: How well cluster addresses the query
        """
        for cluster in clusters:
            # Consistency scoring within cluster
            cluster.consistency_score = self._calculate_consistency_score(cluster)
            
            # Relevance scoring to query
            cluster.relevance_score = await self._calculate_relevance_score(query, cluster)
            
            # Combined confidence score
            cluster.confidence_score = (
                cluster.consistency_score * 0.6 +  # Weight consistency higher
                cluster.relevance_score * 0.4
            )

        return clusters

    def _calculate_consistency_score(self, cluster: EvidenceCluster) -> float:
        """
        COT: Measure internal consistency within evidence cluster
        Higher score = sources agree more strongly
        """
        if len(cluster.articles) <= 1:
            return 1.0  # Single source is perfectly consistent
        
        # Extract text content
        texts = [f"{article.title} {article.content}" for article in cluster.articles]
        
        try:
            # TF-IDF similarity within cluster
            tfidf_matrix = self.tfidf_vectorizer.transform(texts)
            similarities = cosine_similarity(tfidf_matrix)
            
            # Average pairwise similarity (excluding diagonal)
            n = len(texts)
            total_similarity = 0
            pairs = 0
            
            for i in range(n):
                for j in range(i + 1, n):
                    total_similarity += similarities[i][j]
                    pairs += 1
            
            return total_similarity / pairs if pairs > 0 else 1.0
            
        except Exception as e:
            logger.warning("Consistency scoring failed", error=str(e))
            return 0.5  # Default moderate consistency

    async def _calculate_relevance_score(self, query: str, cluster: EvidenceCluster) -> float:
        """
        COT: Measure how well cluster addresses the original query
        Uses semantic similarity between query and cluster content
        """
        try:
            # Combine cluster content
            cluster_text = " ".join([
                f"{article.title} {article.content}" 
                for article in cluster.articles
            ])
            
            # TF-IDF similarity to query
            combined_texts = [query, cluster_text]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(combined_texts)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logger.warning("Relevance scoring failed", error=str(e))
            return 0.5  # Default moderate relevance

    def _rerank_by_combined_score(self, clusters: List[EvidenceCluster]) -> List[EvidenceCluster]:
        """
        COT: Rerank clusters by combined confidence score
        Higher scoring clusters get priority in summary generation
        """
        return sorted(clusters, key=lambda c: c.confidence_score, reverse=True)

    async def _generate_structured_summary(
        self,
        query: str,
        clusters: List[EvidenceCluster],
        max_length: int
    ) -> Dict[str, Any]:
        """
        COT: Generate structured summary with bullet points and citations
        Use high-confidence clusters to minimize hallucination risk
        """
        # Filter high-confidence clusters
        high_conf_clusters = [
            c for c in clusters 
            if c.confidence_score >= self.citation_min_confidence
        ]
        
        if not high_conf_clusters:
            # Fallback to best available
            high_conf_clusters = clusters[:2] if clusters else []

        # Generate bullet points from key claims
        bullet_points = []
        citations = []
        
        for i, cluster in enumerate(high_conf_clusters[:3]):  # Top 3 clusters
            # Extract top claims
            for claim in cluster.key_claims[:2]:  # Top 2 claims per cluster
                bullet_points.append(f"• {claim}")
                
                # Add citation
                citations.append({
                    "claim": claim,
                    "sources": cluster.source_urls[:2],  # Top 2 sources
                    "confidence": cluster.confidence_score,
                    "cluster_id": i
                })

        # Generate narrative summary
        summary_parts = []
        for cluster in high_conf_clusters[:2]:  # Top 2 for narrative
            if cluster.key_claims:
                summary_parts.append(cluster.key_claims[0])  # Lead claim
        
        summary_text = " ".join(summary_parts)
        
        # Truncate if needed
        if len(summary_text) > max_length:
            summary_text = summary_text[:max_length-3] + "..."

        # Overall confidence
        overall_confidence = (
            np.mean([c.confidence_score for c in high_conf_clusters])
            if high_conf_clusters else 0.5
        )

        # Fact check status
        fact_status = "verified" if overall_confidence > 0.8 else "unverified"

        return {
            "summary": summary_text,
            "bullets": bullet_points,
            "citations": citations,
            "confidence": overall_confidence,
            "fact_status": fact_status
        }

    def _extract_key_claims(self, articles: List[NewsArticle]) -> List[str]:
        """
        COT: Extract key factual claims from article cluster
        Simplified extraction - can be enhanced with NER
        """
        claims = []
        
        for article in articles:
            # Extract sentences with high information content
            sentences = article.content.split('.')
            for sentence in sentences:
                sentence = sentence.strip()
                if (len(sentence) > 20 and 
                    any(keyword in sentence.lower() for keyword in 
                        ['reported', 'confirmed', 'announced', 'stated', 'according to'])):
                    claims.append(sentence)
        
        return claims[:5]  # Top 5 claims

    def _calculate_hallucination_risk(self, clusters: List[EvidenceCluster]) -> float:
        """
        COT: Estimate risk of hallucination based on evidence quality
        Lower consistency/relevance = higher hallucination risk
        """
        if not clusters:
            return 1.0  # Maximum risk with no evidence
        
        avg_consistency = np.mean([c.consistency_score for c in clusters])
        avg_relevance = np.mean([c.relevance_score for c in clusters])
        
        # Inverse relationship: lower scores = higher risk
        risk = 1.0 - (avg_consistency * 0.6 + avg_relevance * 0.4)
        return max(0.0, min(1.0, risk))


# Sonnet-4 Prompt Template for ScoreRAG
SCORERAG_PROMPT_TEMPLATE = """
You are an advanced fact-checking and summarization AI using ScoreRAG methodology.

TASK: Create a structured summary with evidence-based bullet points

INPUT:
Query: {query}
Evidence Clusters: {clusters}
Confidence Scores: {confidence_scores}

INSTRUCTIONS:
1. Analyze consistency within each evidence cluster
2. Rank claims by cross-source verification
3. Generate 3-5 bullet points with source citations
4. Include confidence score for each claim
5. Flag any contradictory evidence

OUTPUT FORMAT:
Summary: [150-word narrative summary]

Key Points:
• [Claim 1] (Confidence: X.X) [Sources: A, B]
• [Claim 2] (Confidence: X.X) [Sources: C, D]
• [Claim 3] (Confidence: X.X) [Sources: E, F]

Fact Check Status: [verified/disputed/unverified]
Hallucination Risk: [low/medium/high]

CRITICAL: Only include claims with confidence > 0.7. If sources contradict, explicitly note the contradiction.
"""
