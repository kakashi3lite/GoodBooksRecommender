"""
📚 Context-Aware Book Recommender - MVP Implementation
Senior Lead Engineer: Smart book recommendations based on news content and topics
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from src.core.logging import StructuredLogger
from src.models.hybrid_recommender import HybridRecommender

logger = StructuredLogger(__name__)


@dataclass
class BookMatch:
    """Book matching result with context relevance"""

    book_id: str
    title: str
    author: str
    description: str
    relevance_score: float
    topics_matched: List[str]
    genre: str
    publication_year: Optional[int]
    cover_url: Optional[str]
    buy_url: Optional[str]


class ContextBookRecommender:
    """
    Context-aware book recommendation engine
    Integrates with existing GoodBooksRecommender to provide news-relevant book suggestions
    """

    def __init__(self):
        self.hybrid_recommender = None
        self.topic_book_mapping = self._initialize_topic_mappings()
        self.session = None

    def _initialize_topic_mappings(self) -> Dict[str, List[str]]:
        """Initialize mapping of news topics to book genres/keywords"""
        return {
            # Technology & Innovation
            "technology": [
                "technology",
                "innovation",
                "artificial intelligence",
                "computer science",
                "digital",
            ],
            "ai": [
                "artificial intelligence",
                "machine learning",
                "robotics",
                "automation",
            ],
            "tech": ["technology", "innovation", "startup", "silicon valley"],
            # Politics & Society
            "politics": [
                "politics",
                "government",
                "democracy",
                "policy",
                "political science",
            ],
            "election": ["politics", "democracy", "voting", "campaign", "elections"],
            "government": ["politics", "policy", "public administration", "governance"],
            # Science & Health
            "climate": [
                "climate change",
                "environment",
                "sustainability",
                "ecology",
                "green",
            ],
            "health": ["health", "medicine", "wellness", "medical", "healthcare"],
            "science": ["science", "physics", "chemistry", "biology", "research"],
            "covid": ["pandemic", "public health", "medicine", "epidemiology"],
            # Economics & Business
            "economy": ["economics", "finance", "business", "markets", "investing"],
            "business": ["business", "entrepreneurship", "management", "leadership"],
            "finance": ["finance", "investing", "money", "economics", "markets"],
            # Social Issues
            "education": ["education", "learning", "teaching", "academic", "school"],
            "social": ["sociology", "society", "culture", "social science"],
            "psychology": ["psychology", "mental health", "behavior", "mind"],
            # International & Security
            "war": ["war", "conflict", "military", "strategy", "history"],
            "international": ["international relations", "diplomacy", "geopolitics"],
            "security": ["security", "defense", "intelligence", "cybersecurity"],
            # Culture & History
            "history": ["history", "historical", "biography", "memoir"],
            "culture": ["culture", "society", "anthropology", "cultural studies"],
            "philosophy": ["philosophy", "ethics", "thinking", "wisdom"],
            # Personal Development
            "leadership": [
                "leadership",
                "management",
                "self-help",
                "personal development",
            ],
            "productivity": ["productivity", "time management", "self-improvement"],
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def get_context_recommendations(
        self, topics: List[str], article_content: str = "", n_recommendations: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get book recommendations based on news article context
        Returns list of BookRecommendation objects for the news expansion API
        """
        try:
            async with self:
                # Extract relevant book keywords from topics
                book_keywords = self._extract_book_keywords(topics, article_content)

                if not book_keywords:
                    logger.info(
                        "No relevant book keywords found for topics", topics=topics
                    )
                    return []

                # Get book recommendations using multiple approaches
                recommendations = await self._get_multi_approach_recommendations(
                    book_keywords, topics, n_recommendations
                )

                # Convert to API response format
                book_recommendations = []
                for rec in recommendations:
                    book_recommendations.append(
                        {
                            "title": rec.title,
                            "author": rec.author,
                            "description": rec.description,
                            "relevance_score": rec.relevance_score,
                            "topics_matched": rec.topics_matched,
                            "buy_url": rec.buy_url,
                            "cover_url": rec.cover_url,
                        }
                    )

                logger.info(
                    "Context book recommendations generated",
                    topics=topics,
                    keywords=book_keywords,
                    recommendations_count=len(book_recommendations),
                )

                return book_recommendations

        except Exception as e:
            logger.error(
                "Context book recommendation failed",
                topics=topics,
                error=str(e),
                exc_info=True,
            )
            return []

    def _extract_book_keywords(self, topics: List[str], content: str) -> List[str]:
        """Extract book-relevant keywords from news topics and content"""
        try:
            keywords = set()

            # Map topics to book keywords
            for topic in topics:
                topic_lower = topic.lower()
                for key, book_terms in self.topic_book_mapping.items():
                    if key in topic_lower or any(
                        key_part in topic_lower for key_part in key.split()
                    ):
                        keywords.update(book_terms)

            # Extract additional keywords from content
            if content:
                content_keywords = self._extract_content_keywords(content)
                keywords.update(content_keywords)

            return list(keywords)[:10]  # Limit to top 10 keywords

        except Exception as e:
            logger.error("Keyword extraction failed", error=str(e))
            return []

    def _extract_content_keywords(self, content: str) -> List[str]:
        """Extract relevant keywords from article content"""
        try:
            # Simple keyword extraction using important terms
            important_terms = [
                "innovation",
                "research",
                "study",
                "analysis",
                "report",
                "expert",
                "scientist",
                "professor",
                "author",
                "leader",
                "strategy",
                "method",
                "approach",
                "solution",
                "future",
                "development",
                "growth",
                "change",
                "impact",
                "influence",
            ]

            content_lower = content.lower()
            found_keywords = []

            for term in important_terms:
                if term in content_lower:
                    found_keywords.append(term)

            return found_keywords

        except Exception as e:
            logger.error("Content keyword extraction failed", error=str(e))
            return []

    async def _get_multi_approach_recommendations(
        self, keywords: List[str], topics: List[str], n_recommendations: int
    ) -> List[BookMatch]:
        """Get recommendations using multiple approaches and combine results"""
        try:
            recommendations = []

            # Approach 1: Keyword-based search
            keyword_recs = await self._get_keyword_based_recommendations(
                keywords, n_recommendations
            )
            recommendations.extend(keyword_recs)

            # Approach 2: Topic-based recommendations
            topic_recs = await self._get_topic_based_recommendations(
                topics, n_recommendations
            )
            recommendations.extend(topic_recs)

            # Approach 3: Curated recommendations (fallback)
            if len(recommendations) < n_recommendations:
                curated_recs = await self._get_curated_recommendations(keywords, topics)
                recommendations.extend(curated_recs)

            # Deduplicate and rank by relevance
            seen_titles = set()
            unique_recommendations = []

            for rec in recommendations:
                if rec.title not in seen_titles:
                    seen_titles.add(rec.title)
                    unique_recommendations.append(rec)

            # Sort by relevance score
            unique_recommendations.sort(key=lambda x: x.relevance_score, reverse=True)

            return unique_recommendations[:n_recommendations]

        except Exception as e:
            logger.error("Multi-approach recommendation failed", error=str(e))
            return []

    async def _get_keyword_based_recommendations(
        self, keywords: List[str], limit: int
    ) -> List[BookMatch]:
        """Get recommendations based on keyword matching"""
        try:
            # Simulate keyword-based book search
            # In production, this would query the actual GoodBooks database
            keyword_books = [
                {
                    "title": "The Innovator's Dilemma",
                    "author": "Clayton M. Christensen",
                    "description": "Why new technologies cause great firms to fail",
                    "keywords": ["innovation", "technology", "business", "disruption"],
                    "genre": "business",
                    "year": 1997,
                },
                {
                    "title": "Sapiens: A Brief History of Humankind",
                    "author": "Yuval Noah Harari",
                    "description": "How humans came to rule the world",
                    "keywords": ["history", "society", "culture", "evolution"],
                    "genre": "history",
                    "year": 2011,
                },
                {
                    "title": "Thinking, Fast and Slow",
                    "author": "Daniel Kahneman",
                    "description": "The psychology of human judgment and decision-making",
                    "keywords": ["psychology", "thinking", "behavior", "science"],
                    "genre": "psychology",
                    "year": 2011,
                },
                {
                    "title": "The Fourth Industrial Revolution",
                    "author": "Klaus Schwab",
                    "description": "How technology is transforming our world",
                    "keywords": ["technology", "future", "innovation", "ai"],
                    "genre": "technology",
                    "year": 2016,
                },
                {
                    "title": "Freakonomics",
                    "author": "Steven D. Levitt",
                    "description": "A rogue economist explores the hidden side of everything",
                    "keywords": ["economics", "analysis", "data", "society"],
                    "genre": "economics",
                    "year": 2005,
                },
            ]

            recommendations = []

            for book in keyword_books:
                # Calculate relevance score based on keyword matches
                matched_keywords = []
                relevance_score = 0.0

                for keyword in keywords:
                    if any(
                        keyword.lower() in book_keyword.lower()
                        for book_keyword in book["keywords"]
                    ):
                        matched_keywords.append(keyword)
                        relevance_score += 0.2

                # Boost score for exact matches
                for book_keyword in book["keywords"]:
                    if book_keyword.lower() in [k.lower() for k in keywords]:
                        relevance_score += 0.3

                if relevance_score > 0.1:  # Threshold for relevance
                    recommendations.append(
                        BookMatch(
                            book_id=f"book_{hash(book['title'])}",
                            title=book["title"],
                            author=book["author"],
                            description=book["description"],
                            relevance_score=min(relevance_score, 1.0),
                            topics_matched=matched_keywords,
                            genre=book["genre"],
                            publication_year=book["year"],
                            cover_url=f"https://covers.openlibrary.org/b/title/{book['title'].replace(' ', '+')}-M.jpg",
                            buy_url=f"https://www.amazon.com/s?k={book['title'].replace(' ', '+')}",
                        )
                    )

            return recommendations[:limit]

        except Exception as e:
            logger.error("Keyword-based recommendation failed", error=str(e))
            return []

    async def _get_topic_based_recommendations(
        self, topics: List[str], limit: int
    ) -> List[BookMatch]:
        """Get recommendations based on topic categories"""
        try:
            # Topic-specific book collections
            topic_collections = {
                "technology": [
                    {
                        "title": "The Code Breaker",
                        "author": "Walter Isaacson",
                        "description": "Jennifer Doudna, gene editing, and the future of the human race",
                        "genre": "biography",
                    }
                ],
                "politics": [
                    {
                        "title": "Democracy in One Book or Less",
                        "author": "David Litt",
                        "description": "How it works, why it doesn't, and why fixing it is easier than you think",
                        "genre": "politics",
                    }
                ],
                "science": [
                    {
                        "title": "The Gene: An Intimate History",
                        "author": "Siddhartha Mukherjee",
                        "description": "From Darwin's theory to modern genetic engineering",
                        "genre": "science",
                    }
                ],
            }

            recommendations = []

            for topic in topics:
                topic_lower = topic.lower()
                for collection_key, books in topic_collections.items():
                    if collection_key in topic_lower:
                        for book in books:
                            recommendations.append(
                                BookMatch(
                                    book_id=f"topic_{hash(book['title'])}",
                                    title=book["title"],
                                    author=book["author"],
                                    description=book["description"],
                                    relevance_score=0.8,  # High relevance for topic matches
                                    topics_matched=[topic],
                                    genre=book["genre"],
                                    publication_year=2020,  # Default year
                                    cover_url=f"https://covers.openlibrary.org/b/title/{book['title'].replace(' ', '+')}-M.jpg",
                                    buy_url=f"https://www.amazon.com/s?k={book['title'].replace(' ', '+')}",
                                )
                            )

            return recommendations[:limit]

        except Exception as e:
            logger.error("Topic-based recommendation failed", error=str(e))
            return []

    async def _get_curated_recommendations(
        self, keywords: List[str], topics: List[str]
    ) -> List[BookMatch]:
        """Get curated recommendations as fallback"""
        try:
            # High-quality books that work well for most news contexts
            curated_books = [
                {
                    "title": "Factfulness",
                    "author": "Hans Rosling",
                    "description": "Ten reasons we're wrong about the world—and why things are better than you think",
                    "relevance": 0.7,
                },
                {
                    "title": "The Signal and the Noise",
                    "author": "Nate Silver",
                    "description": "Why so many predictions fail—but some don't",
                    "relevance": 0.6,
                },
                {
                    "title": "Outliers",
                    "author": "Malcolm Gladwell",
                    "description": "The story of success and what makes high-achievers different",
                    "relevance": 0.6,
                },
            ]

            recommendations = []

            for book in curated_books:
                recommendations.append(
                    BookMatch(
                        book_id=f"curated_{hash(book['title'])}",
                        title=book["title"],
                        author=book["author"],
                        description=book["description"],
                        relevance_score=book["relevance"],
                        topics_matched=topics[:2],  # Match first 2 topics
                        genre="general",
                        publication_year=2010,  # Default
                        cover_url=f"https://covers.openlibrary.org/b/title/{book['title'].replace(' ', '+')}-M.jpg",
                        buy_url=f"https://www.amazon.com/s?k={book['title'].replace(' ', '+')}",
                    )
                )

            return recommendations

        except Exception as e:
            logger.error("Curated recommendation failed", error=str(e))
            return []


# Standalone function for easy integration
async def get_books_for_news(
    topics: List[str], content: str = "", limit: int = 5
) -> List[Dict[str, Any]]:
    """Quick book recommendation function for news context"""
    recommender = ContextBookRecommender()
    return await recommender.get_context_recommendations(topics, content, limit)
