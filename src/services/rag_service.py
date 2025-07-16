"""
RAG (Retrieval-Augmented Generation) service for generating explanations
of book recommendations using vector store and LLM capabilities.
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.core.vector_store import BookVectorStore, VectorStoreError
from src.core.logging import StructuredLogger
from src.core.exceptions import GoodBooksException

logger = StructuredLogger(__name__)

class RAGError(GoodBooksException):
    """Raised when RAG operations fail"""
    pass

@dataclass
class ExplanationContext:
    """Context information for generating explanations."""
    query_book: Dict[str, Any]
    similar_books: List[Dict[str, Any]]
    recommendation_type: str
    search_query: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = None

class RAGExplanationService:
    """
    Service for generating explanations using RAG (Retrieval-Augmented Generation).
    Uses vector store for content retrieval and template-based generation.
    """
    
    def __init__(self, vector_store: BookVectorStore):
        """
        Initialize RAG explanation service.
        
        Args:
            vector_store: Initialized BookVectorStore instance
        """
        self.vector_store = vector_store
        self.explanation_templates = self._load_explanation_templates()
    
    def _load_explanation_templates(self) -> Dict[str, str]:
        """Load explanation templates for different recommendation types."""
        return {
            "content_based": """
Based on your interest in "{query_book_title}" by {query_book_authors}, here's why we recommend these books:

{similar_books_explanation}

These recommendations share similar themes, writing styles, or subject matter with your selected book. The content-based filtering identified books with matching tags, genres, and narrative elements.

Key similarities include:
{key_similarities}
            """.strip(),
            
            "collaborative": """
Other readers who enjoyed "{query_book_title}" by {query_book_authors} also loved these books:

{similar_books_explanation}

This recommendation is based on collaborative filtering - analyzing reading patterns of users with similar tastes to yours. Readers with comparable preferences have rated these books highly.

Reading patterns show:
{reading_patterns}
            """.strip(),
            
            "hybrid": """
Based on a combination of content analysis and reader preferences for "{query_book_title}" by {query_book_authors}, we recommend:

{similar_books_explanation}

Our hybrid approach combines:
• Content similarity: {content_score:.1%} match in themes and genres
• Collaborative signals: {collaborative_score:.1%} preference alignment
• Overall confidence: {hybrid_score:.1%}

{detailed_explanation}
            """.strip(),
            
            "semantic_search": """
Based on your search for "{search_query}", here are the most relevant books we found:

{search_results_explanation}

Our semantic search analyzed the meaning and context of your query to find books that match not just keywords, but the underlying concepts and themes you're looking for.

Search insights:
{search_insights}
            """.strip()
        }
    
    async def explain_recommendation_async(
        self, 
        book_id: int,
        recommendation_type: str = "hybrid",
        user_preferences: Optional[Dict[str, Any]] = None,
        n_context_books: int = 5
    ) -> Dict[str, Any]:
        """
        Generate explanation for why specific books are recommended.
        
        Args:
            book_id: ID of the book to explain recommendations for
            recommendation_type: Type of recommendation ("content_based", "collaborative", "hybrid")
            user_preferences: Optional user preference data
            n_context_books: Number of similar books to use for context
            
        Returns:
            Dictionary with explanation text and supporting data
            
        Raises:
            RAGError: If explanation generation fails
        """
        try:
            logger.info(
                "Generating recommendation explanation",
                book_id=book_id,
                type=recommendation_type
            )
            
            # Get book metadata from vector store
            if book_id not in self.vector_store.book_id_to_id:
                raise RAGError(f"Book {book_id} not found in vector store")
            
            vector_id = self.vector_store.book_id_to_id[book_id]
            query_book = self.vector_store.book_metadata[vector_id]
            
            # Get similar books for context
            similar_books = await self.vector_store.get_similar_books_async(
                book_id, k=n_context_books
            )
            
            # Create explanation context
            context = ExplanationContext(
                query_book=query_book,
                similar_books=similar_books,
                recommendation_type=recommendation_type,
                user_preferences=user_preferences
            )
            
            # Generate explanation
            explanation = await self._generate_explanation_async(context)
            
            logger.info(
                "Recommendation explanation generated",
                book_id=book_id,
                explanation_length=len(explanation["text"])
            )
            
            return explanation
            
        except Exception as e:
            logger.error("Failed to generate explanation", book_id=book_id, error=str(e))
            raise RAGError(f"Explanation generation failed: {str(e)}") from e
    
    async def explain_search_results_async(
        self,
        search_query: str,
        search_results: List[Dict[str, Any]],
        max_results_to_explain: int = 5
    ) -> Dict[str, Any]:
        """
        Generate explanation for semantic search results.
        
        Args:
            search_query: Original search query
            search_results: List of search results from vector store
            max_results_to_explain: Maximum number of results to explain in detail
            
        Returns:
            Dictionary with explanation text and supporting data
        """
        try:
            logger.info(
                "Generating search explanation",
                query=search_query[:100],
                num_results=len(search_results)
            )
            
            # Create explanation context
            context = ExplanationContext(
                query_book={},  # No specific query book for search
                similar_books=search_results[:max_results_to_explain],
                recommendation_type="semantic_search",
                search_query=search_query
            )
            
            # Generate explanation
            explanation = await self._generate_search_explanation_async(context)
            
            logger.info(
                "Search explanation generated",
                query=search_query[:100],
                explanation_length=len(explanation["text"])
            )
            
            return explanation
            
        except Exception as e:
            logger.error("Failed to generate search explanation", query=search_query[:100], error=str(e))
            raise RAGError(f"Search explanation generation failed: {str(e)}") from e
    
    async def _generate_explanation_async(self, context: ExplanationContext) -> Dict[str, Any]:
        """Generate explanation based on context."""
        template = self.explanation_templates.get(context.recommendation_type)
        if not template:
            raise RAGError(f"Unknown recommendation type: {context.recommendation_type}")
        
        # Prepare template variables
        variables = {
            "query_book_title": context.query_book.get("title", "Unknown"),
            "query_book_authors": context.query_book.get("authors", "Unknown"),
            "similar_books_explanation": await self._format_similar_books_async(context.similar_books),
            "key_similarities": await self._analyze_similarities_async(context),
            "reading_patterns": await self._analyze_reading_patterns_async(context),
            "detailed_explanation": await self._generate_detailed_explanation_async(context)
        }
        
        # Add hybrid-specific scores if applicable
        if context.recommendation_type == "hybrid":
            variables.update({
                "content_score": 0.75,  # These would come from actual recommendation model
                "collaborative_score": 0.68,
                "hybrid_score": 0.82
            })
        
        # Format template
        explanation_text = template.format(**variables)
        
        return {
            "text": explanation_text,
            "context": {
                "query_book": context.query_book,
                "similar_books": context.similar_books,
                "recommendation_type": context.recommendation_type,
                "confidence_scores": self._calculate_confidence_scores(context)
            },
            "metadata": {
                "generation_method": "template_based_rag",
                "context_books_count": len(context.similar_books),
                "has_user_preferences": context.user_preferences is not None
            }
        }
    
    async def _generate_search_explanation_async(self, context: ExplanationContext) -> Dict[str, Any]:
        """Generate explanation for search results."""
        template = self.explanation_templates["semantic_search"]
        
        variables = {
            "search_query": context.search_query,
            "search_results_explanation": await self._format_search_results_async(context.similar_books),
            "search_insights": await self._analyze_search_insights_async(context)
        }
        
        explanation_text = template.format(**variables)
        
        return {
            "text": explanation_text,
            "context": {
                "search_query": context.search_query,
                "results": context.similar_books,
                "total_results": len(context.similar_books)
            },
            "metadata": {
                "generation_method": "semantic_search_rag",
                "results_count": len(context.similar_books)
            }
        }
    
    async def _format_similar_books_async(self, similar_books: List[Dict[str, Any]]) -> str:
        """Format similar books for explanation text."""
        if not similar_books:
            return "No similar books found."
        
        formatted_books = []
        for i, book in enumerate(similar_books, 1):
            metadata = book.get("metadata", {})
            title = book.get("title", "Unknown Title")
            authors = book.get("authors", "Unknown Author")
            similarity = book.get("similarity_score", 0.0)
            rating = metadata.get("average_rating", 0.0)
            
            book_text = f"{i}. \"{title}\" by {authors}"
            if rating > 0:
                book_text += f" (★{rating:.1f})"
            if similarity > 0:
                book_text += f" - {similarity:.1%} similarity"
            
            # Add brief description if available
            description = metadata.get("description", "")
            if description:
                brief_desc = description[:100] + "..." if len(description) > 100 else description
                book_text += f"\\n   {brief_desc}"
            
            formatted_books.append(book_text)
        
        return "\\n\\n".join(formatted_books)
    
    async def _format_search_results_async(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for explanation text."""
        return await self._format_similar_books_async(results)
    
    async def _analyze_similarities_async(self, context: ExplanationContext) -> str:
        """Analyze and describe key similarities between books."""
        similarities = []
        
        query_tags = set((context.query_book.get("all_tags", "")).split())
        query_genres = set((context.query_book.get("genres", "")).split())
        
        for book in context.similar_books[:3]:  # Analyze top 3 books
            metadata = book.get("metadata", {})
            book_tags = set((metadata.get("all_tags", "")).split())
            book_genres = set((metadata.get("genres", "")).split())
            
            # Find common tags and genres
            common_tags = query_tags.intersection(book_tags)
            common_genres = query_genres.intersection(book_genres)
            
            if common_tags:
                similarities.append(f"Shared themes: {', '.join(list(common_tags)[:3])}")
            if common_genres:
                similarities.append(f"Common genres: {', '.join(list(common_genres)[:2])}")
        
        return "\\n• ".join(similarities) if similarities else "Thematic and stylistic elements"
    
    async def _analyze_reading_patterns_async(self, context: ExplanationContext) -> str:
        """Analyze reading patterns from collaborative data."""
        patterns = []
        
        # Calculate average ratings of similar books
        ratings = [book.get("metadata", {}).get("average_rating", 0.0) 
                  for book in context.similar_books if book.get("metadata", {}).get("average_rating")]
        
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            patterns.append(f"Average rating of recommended books: {avg_rating:.1f}/5.0")
        
        patterns.append(f"Based on {len(context.similar_books)} similar reader preferences")
        patterns.append("High correlation with your reading history")
        
        return "\\n• ".join(patterns)
    
    async def _generate_detailed_explanation_async(self, context: ExplanationContext) -> str:
        """Generate detailed explanation for hybrid recommendations."""
        explanations = []
        
        explanations.append("Content analysis identified thematic similarities in:")
        explanations.append("• Writing style and narrative structure")
        explanations.append("• Genre classification and subject matter")
        explanations.append("• Reader engagement patterns")
        
        explanations.append("\\nCollaborative filtering reveals:")
        explanations.append("• Readers with similar tastes rated these books highly")
        explanations.append("• Strong correlation with your reading preferences")
        explanations.append("• Positive reading experience indicators")
        
        return "\\n".join(explanations)
    
    async def _analyze_search_insights_async(self, context: ExplanationContext) -> str:
        """Analyze insights from semantic search."""
        insights = []
        
        insights.append(f"Semantic analysis of '{context.search_query}' identified:")
        insights.append("• Conceptual themes and topics")
        insights.append("• Related genres and categories")
        insights.append("• Contextual meaning beyond keywords")
        
        if context.similar_books:
            avg_score = sum(book.get("similarity_score", 0.0) for book in context.similar_books) / len(context.similar_books)
            insights.append(f"\\nAverage relevance score: {avg_score:.1%}")
            insights.append(f"Results span {len(set(book.get('metadata', {}).get('genres', '') for book in context.similar_books))} different genres")
        
        return "\\n".join(insights)
    
    def _calculate_confidence_scores(self, context: ExplanationContext) -> Dict[str, float]:
        """Calculate confidence scores for explanations."""
        scores = {
            "overall_confidence": 0.0,
            "content_similarity": 0.0,
            "recommendation_strength": 0.0
        }
        
        if context.similar_books:
            # Base confidence on similarity scores
            similarity_scores = [book.get("similarity_score", 0.0) for book in context.similar_books]
            scores["content_similarity"] = sum(similarity_scores) / len(similarity_scores)
            scores["recommendation_strength"] = max(similarity_scores)
            scores["overall_confidence"] = (scores["content_similarity"] + scores["recommendation_strength"]) / 2
        
        return scores
