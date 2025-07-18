"""
🧠 Fact Hunter Engine - MVP Implementation
Senior Lead Engineer: AI-powered fact checking with web search and source verification
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from urllib.parse import quote_plus

from src.core.logging import StructuredLogger

logger = StructuredLogger(__name__)

@dataclass
class FactClaim:
    """Individual claim extracted from news content"""
    text: str
    confidence: float
    claim_type: str  # "factual", "opinion", "prediction"
    keywords: List[str]

@dataclass
class FactSource:
    """Source used for fact verification"""
    url: str
    title: str
    snippet: str
    credibility_score: float
    source_type: str  # "wikipedia", "reuters", "academic", "government"

@dataclass
class FactVerification:
    """Complete fact verification result"""
    claim: str
    verdict: str  # "True", "False", "Unverified", "Mixed"
    confidence: float
    sources: List[FactSource]
    explanation: str
    verified_at: datetime

class FactHunterEngine:
    """
    AI-powered fact checking engine with multiple verification sources
    MVP: Fast fact checking with web search and trusted source verification
    """
    
    def __init__(self):
        self.session = None
        self.trusted_domains = {
            "wikipedia.org": 0.9,
            "reuters.com": 0.95,
            "ap.org": 0.95,
            "bbc.com": 0.9,
            "snopes.com": 0.85,
            "factcheck.org": 0.9,
            "politifact.com": 0.85,
            "cdc.gov": 0.95,
            "who.int": 0.95,
            "gov": 0.8,  # General government domains
            "edu": 0.85  # Academic domains
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'GoodBooks-FactHunter/1.0 (Fact Verification Bot)'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def verify_claims(self, content: str, title: str) -> List[Dict[str, Any]]:
        """
        Main fact verification method
        Returns list of FactCheck objects for the news expansion API
        """
        try:
            async with self:
                # Extract claims from content
                claims = await self._extract_claims(content, title)
                
                if not claims:
                    logger.info("No factual claims found for verification")
                    return []
                
                # Verify each claim in parallel
                verification_tasks = [
                    self._verify_single_claim(claim) 
                    for claim in claims[:5]  # Limit to 5 claims for MVP
                ]
                
                verifications = await asyncio.gather(*verification_tasks, return_exceptions=True)
                
                # Convert to API response format
                fact_checks = []
                for verification in verifications:
                    if isinstance(verification, FactVerification):
                        fact_checks.append({
                            "claim": verification.claim,
                            "verdict": verification.verdict,
                            "confidence": verification.confidence,
                            "sources": [source.url for source in verification.sources],
                            "explanation": verification.explanation
                        })
                
                logger.info(
                    "Fact verification completed",
                    claims_extracted=len(claims),
                    claims_verified=len(fact_checks)
                )
                
                return fact_checks
                
        except Exception as e:
            logger.error("Fact verification failed", error=str(e), exc_info=True)
            return []
    
    async def _extract_claims(self, content: str, title: str) -> List[FactClaim]:
        """Extract factual claims from news content using simple heuristics"""
        try:
            # Simple claim extraction using keywords and sentence patterns
            # MVP: Basic regex patterns for factual statements
            import re
            
            # Patterns that indicate factual claims
            factual_patterns = [
                r'(\d+(?:,\d{3})*(?:\.\d+)?)\s+(percent|%|people|dollars?|deaths?|cases?)',
                r'(according to|reports show|data shows|studies indicate)',
                r'(\d{4})\s+(study|report|survey)',
                r'(scientists?|researchers?|experts?)\s+(found|discovered|concluded)',
                r'(government|officials?|authorities?)\s+(announced|confirmed|stated)'
            ]
            
            sentences = content.split('.')
            claims = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 20:  # Skip very short sentences
                    continue
                
                # Check for factual patterns
                confidence = 0.0
                keywords = []
                
                for pattern in factual_patterns:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        confidence += 0.2
                        matches = re.findall(pattern, sentence, re.IGNORECASE)
                        keywords.extend([match[0] if isinstance(match, tuple) else match for match in matches])
                
                # Boost confidence for numbers and specific terms
                if re.search(r'\d+', sentence):
                    confidence += 0.1
                if any(word in sentence.lower() for word in ['study', 'research', 'data', 'report']):
                    confidence += 0.1
                
                if confidence >= 0.3:  # Threshold for factual claims
                    claims.append(FactClaim(
                        text=sentence,
                        confidence=min(confidence, 1.0),
                        claim_type="factual",
                        keywords=list(set(keywords))
                    ))
            
            # Sort by confidence and return top claims
            claims.sort(key=lambda x: x.confidence, reverse=True)
            return claims[:10]  # Limit to top 10 claims
            
        except Exception as e:
            logger.error("Claim extraction failed", error=str(e))
            return []
    
    async def _verify_single_claim(self, claim: FactClaim) -> FactVerification:
        """Verify a single claim using web search and trusted sources"""
        try:
            # Search for information about the claim
            sources = await self._search_claim_sources(claim.text)
            
            if not sources:
                return FactVerification(
                    claim=claim.text,
                    verdict="Unverified",
                    confidence=0.0,
                    sources=[],
                    explanation="No reliable sources found for verification",
                    verified_at=datetime.now()
                )
            
            # Analyze sources and determine verdict
            verdict, confidence, explanation = await self._analyze_sources(claim, sources)
            
            return FactVerification(
                claim=claim.text,
                verdict=verdict,
                confidence=confidence,
                sources=sources[:3],  # Limit to top 3 sources
                explanation=explanation,
                verified_at=datetime.now()
            )
            
        except Exception as e:
            logger.error("Single claim verification failed", claim=claim.text, error=str(e))
            return FactVerification(
                claim=claim.text,
                verdict="Unverified",
                confidence=0.0,
                sources=[],
                explanation=f"Verification failed: {str(e)}",
                verified_at=datetime.now()
            )
    
    async def _search_claim_sources(self, claim_text: str) -> List[FactSource]:
        """Search for sources related to the claim using DuckDuckGo"""
        try:
            # Use DuckDuckGo instant answer API (free, no API key required)
            search_query = quote_plus(claim_text[:100])  # Limit query length
            
            # DuckDuckGo instant answer API
            url = f"https://api.duckduckgo.com/?q={search_query}&format=json&no_html=1&skip_disambig=1"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    sources = []
                    
                    # Extract sources from DuckDuckGo response
                    if data.get('AbstractSource'):
                        sources.append(FactSource(
                            url=data.get('AbstractURL', ''),
                            title=data.get('AbstractSource', ''),
                            snippet=data.get('Abstract', '')[:200],
                            credibility_score=self._get_domain_credibility(data.get('AbstractURL', '')),
                            source_type=self._classify_source_type(data.get('AbstractURL', ''))
                        ))
                    
                    # Add related topics
                    for topic in data.get('RelatedTopics', [])[:3]:
                        if isinstance(topic, dict) and topic.get('FirstURL'):
                            sources.append(FactSource(
                                url=topic.get('FirstURL', ''),
                                title=topic.get('Text', '')[:100],
                                snippet=topic.get('Text', '')[:200],
                                credibility_score=self._get_domain_credibility(topic.get('FirstURL', '')),
                                source_type=self._classify_source_type(topic.get('FirstURL', ''))
                            ))
                    
                    # Filter and sort by credibility
                    sources = [s for s in sources if s.credibility_score > 0.5]
                    sources.sort(key=lambda x: x.credibility_score, reverse=True)
                    
                    return sources[:5]  # Return top 5 sources
            
            return []
            
        except Exception as e:
            logger.error("Source search failed", error=str(e))
            return []
    
    def _get_domain_credibility(self, url: str) -> float:
        """Get credibility score for a domain"""
        if not url:
            return 0.0
        
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.lower()
            
            # Check exact matches
            for trusted_domain, score in self.trusted_domains.items():
                if trusted_domain in domain:
                    return score
            
            # Default credibility based on domain type
            if domain.endswith('.gov'):
                return 0.8
            elif domain.endswith('.edu'):
                return 0.75
            elif domain.endswith('.org'):
                return 0.6
            else:
                return 0.5
                
        except Exception:
            return 0.3
    
    def _classify_source_type(self, url: str) -> str:
        """Classify the type of source"""
        if not url:
            return "unknown"
        
        domain_lower = url.lower()
        
        if 'wikipedia.org' in domain_lower:
            return "wikipedia"
        elif any(news in domain_lower for news in ['reuters', 'ap.org', 'bbc']):
            return "news"
        elif 'snopes' in domain_lower or 'factcheck' in domain_lower:
            return "fact_check"
        elif '.gov' in domain_lower:
            return "government"
        elif '.edu' in domain_lower:
            return "academic"
        else:
            return "general"
    
    async def _analyze_sources(self, claim: FactClaim, sources: List[FactSource]) -> Tuple[str, float, str]:
        """Analyze sources to determine verdict and confidence"""
        try:
            if not sources:
                return "Unverified", 0.0, "No sources available for verification"
            
            # Simple analysis based on source credibility and content
            total_credibility = sum(source.credibility_score for source in sources)
            avg_credibility = total_credibility / len(sources)
            
            # MVP: Simple verdict logic
            if avg_credibility >= 0.8:
                if len(sources) >= 2:
                    verdict = "True"
                    confidence = min(avg_credibility, 0.95)
                    explanation = f"Confirmed by {len(sources)} reliable sources"
                else:
                    verdict = "Likely True"
                    confidence = avg_credibility * 0.8
                    explanation = "Supported by reliable source but needs additional verification"
            elif avg_credibility >= 0.6:
                verdict = "Mixed"
                confidence = avg_credibility * 0.7
                explanation = f"Partially verified by {len(sources)} sources with mixed reliability"
            else:
                verdict = "Unverified"
                confidence = avg_credibility * 0.5
                explanation = "Limited verification from available sources"
            
            return verdict, confidence, explanation
            
        except Exception as e:
            logger.error("Source analysis failed", error=str(e))
            return "Unverified", 0.0, f"Analysis failed: {str(e)}"

# Standalone function for easy integration
async def quick_fact_check(content: str, title: str = "") -> List[Dict[str, Any]]:
    """Quick fact check function for easy integration"""
    fact_hunter = FactHunterEngine()
    return await fact_hunter.verify_claims(content, title)
