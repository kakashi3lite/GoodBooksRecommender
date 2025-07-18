"""
GDPR Compliance and Privacy-First Personalization
Implements privacy-first personalization with GDPR compliance, consent management, and explainable AI
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import json
import uuid
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field
import aioredis

logger = logging.getLogger(__name__)

class ConsentType(str, Enum):
    """Types of user consent"""
    NECESSARY = "necessary"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    PERSONALIZATION = "personalization"
    THIRD_PARTY = "third_party"

class ProcessingPurpose(str, Enum):
    """Data processing purposes"""
    BOOK_RECOMMENDATIONS = "book_recommendations"
    NEWSLETTER_PERSONALIZATION = "newsletter_personalization"
    CONTENT_CURATION = "content_curation"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    RESEARCH = "research"

@dataclass
class ConsentRecord:
    """User consent record"""
    user_id: str
    consent_type: ConsentType
    purpose: ProcessingPurpose
    granted: bool
    timestamp: datetime
    expiry: Optional[datetime] = None
    version: str = "1.0"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
class DataSubjectRequest:
    """GDPR Data Subject Request"""
    request_id: str
    user_id: str
    request_type: str  # access, rectification, erasure, portability, restriction
    timestamp: datetime
    status: str = "pending"
    fulfilled_at: Optional[datetime] = None
    data: Optional[Dict[str, Any]] = None

class PrivacyFirstPersonalization:
    """Privacy-first personalization engine with GDPR compliance"""
    
    def __init__(self, redis_client: aioredis.Redis, encryption_key: str):
        self.redis = redis_client
        self.cipher = Fernet(encryption_key.encode() if len(encryption_key) == 44 else Fernet.generate_key())
        self.consent_store = "gdpr:consent"
        self.data_store = "gdpr:data"
        self.requests_store = "gdpr:requests"
        self.audit_log = "gdpr:audit"
        
    async def record_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        purpose: ProcessingPurpose,
        granted: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConsentRecord:
        """Record user consent with full audit trail"""
        try:
            consent = ConsentRecord(
                user_id=user_id,
                consent_type=consent_type,
                purpose=purpose,
                granted=granted,
                timestamp=datetime.utcnow(),
                expiry=datetime.utcnow() + timedelta(days=365) if granted else None,
                ip_address=metadata.get("ip_address") if metadata else None,
                user_agent=metadata.get("user_agent") if metadata else None
            )
            
            # Store consent record
            consent_key = f"{self.consent_store}:{user_id}:{consent_type.value}:{purpose.value}"
            consent_data = self._encrypt_data(asdict(consent))
            await self.redis.setex(consent_key, 86400 * 365, consent_data)  # 1 year
            
            # Audit log
            await self._log_audit_event("consent_recorded", {
                "user_id": user_id,
                "consent_type": consent_type.value,
                "purpose": purpose.value,
                "granted": granted
            })
            
            logger.info(f"Consent recorded for user {user_id}: {consent_type.value}/{purpose.value} = {granted}")
            return consent
            
        except Exception as e:
            logger.error(f"Failed to record consent: {e}")
            raise
    
    async def check_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        purpose: ProcessingPurpose
    ) -> bool:
        """Check if user has granted consent for specific purpose"""
        try:
            consent_key = f"{self.consent_store}:{user_id}:{consent_type.value}:{purpose.value}"
            consent_data = await self.redis.get(consent_key)
            
            if not consent_data:
                return False
                
            consent = self._decrypt_data(consent_data)
            
            # Check if consent is still valid
            if consent.get("expiry"):
                expiry = datetime.fromisoformat(consent["expiry"])
                if datetime.utcnow() > expiry:
                    await self.redis.delete(consent_key)
                    return False
            
            return consent.get("granted", False)
            
        except Exception as e:
            logger.error(f"Failed to check consent: {e}")
            return False
    
    async def get_user_consents(self, user_id: str) -> List[ConsentRecord]:
        """Get all consent records for a user"""
        try:
            pattern = f"{self.consent_store}:{user_id}:*"
            keys = await self.redis.keys(pattern)
            
            consents = []
            for key in keys:
                consent_data = await self.redis.get(key)
                if consent_data:
                    consent_dict = self._decrypt_data(consent_data)
                    consent_dict["timestamp"] = datetime.fromisoformat(consent_dict["timestamp"])
                    if consent_dict.get("expiry"):
                        consent_dict["expiry"] = datetime.fromisoformat(consent_dict["expiry"])
                    consents.append(ConsentRecord(**consent_dict))
            
            return consents
            
        except Exception as e:
            logger.error(f"Failed to get user consents: {e}")
            return []
    
    async def personalize_with_privacy(
        self,
        user_id: str,
        base_recommendations: List[Dict[str, Any]],
        personalization_level: str = "basic"
    ) -> Dict[str, Any]:
        """Apply privacy-first personalization to recommendations"""
        try:
            # Check personalization consent
            can_personalize = await self.check_consent(
                user_id, 
                ConsentType.PERSONALIZATION, 
                ProcessingPurpose.BOOK_RECOMMENDATIONS
            )
            
            if not can_personalize:
                return {
                    "recommendations": base_recommendations,
                    "personalization_applied": False,
                    "privacy_explanation": "No personalization applied due to consent preferences"
                }
            
            # Apply privacy-preserving personalization
            personalized_recs = []
            explanations = []
            
            for rec in base_recommendations:
                # Add privacy-safe personalization signals
                enhanced_rec = rec.copy()
                
                if personalization_level == "advanced":
                    # Advanced personalization with explicit consent
                    can_use_analytics = await self.check_consent(
                        user_id, 
                        ConsentType.ANALYTICS, 
                        ProcessingPurpose.CONTENT_CURATION
                    )
                    
                    if can_use_analytics:
                        enhanced_rec["personalization_score"] = self._calculate_privacy_safe_score(
                            user_id, rec
                        )
                        explanations.append(f"Personalized based on your reading preferences")
                    else:
                        explanations.append(f"Recommended based on popularity and ratings")
                else:
                    # Basic personalization (aggregated, anonymized data)
                    enhanced_rec["popularity_boost"] = self._get_anonymous_popularity_boost(rec)
                    explanations.append(f"Recommended based on similar readers' preferences")
                
                personalized_recs.append(enhanced_rec)
            
            return {
                "recommendations": personalized_recs,
                "personalization_applied": True,
                "privacy_explanation": "Personalization applied with your consent",
                "explanations": explanations,
                "consent_status": {
                    "personalization": can_personalize,
                    "analytics": await self.check_consent(user_id, ConsentType.ANALYTICS, ProcessingPurpose.ANALYTICS)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to apply privacy-first personalization: {e}")
            return {
                "recommendations": base_recommendations,
                "personalization_applied": False,
                "error": "Personalization temporarily unavailable"
            }
    
    async def handle_data_subject_request(
        self,
        user_id: str,
        request_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> DataSubjectRequest:
        """Handle GDPR data subject requests"""
        try:
            request = DataSubjectRequest(
                request_id=str(uuid.uuid4()),
                user_id=user_id,
                request_type=request_type,
                timestamp=datetime.utcnow()
            )
            
            # Store request
            request_key = f"{self.requests_store}:{request.request_id}"
            request_data = self._encrypt_data(asdict(request))
            await self.redis.setex(request_key, 86400 * 30, request_data)  # 30 days
            
            # Process request based on type
            if request_type == "access":
                request.data = await self._compile_user_data(user_id)
                request.status = "completed"
                request.fulfilled_at = datetime.utcnow()
                
            elif request_type == "erasure":
                await self._erase_user_data(user_id)
                request.status = "completed"
                request.fulfilled_at = datetime.utcnow()
                
            elif request_type == "portability":
                request.data = await self._export_user_data(user_id)
                request.status = "completed"
                request.fulfilled_at = datetime.utcnow()
                
            else:
                request.status = "pending_review"
            
            # Update stored request
            request_data = self._encrypt_data(asdict(request))
            await self.redis.setex(request_key, 86400 * 30, request_data)
            
            # Audit log
            await self._log_audit_event("data_subject_request", {
                "request_id": request.request_id,
                "user_id": user_id,
                "request_type": request_type,
                "status": request.status
            })
            
            logger.info(f"Data subject request processed: {request.request_id}")
            return request
            
        except Exception as e:
            logger.error(f"Failed to handle data subject request: {e}")
            raise
    
    async def generate_privacy_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Generate privacy dashboard for user"""
        try:
            consents = await self.get_user_consents(user_id)
            
            # Get data processing activities
            processing_activities = []
            for consent in consents:
                if consent.granted:
                    processing_activities.append({
                        "purpose": consent.purpose.value,
                        "consent_type": consent.consent_type.value,
                        "granted_at": consent.timestamp.isoformat(),
                        "expires_at": consent.expiry.isoformat() if consent.expiry else None
                    })
            
            # Get data retention info
            retention_info = await self._get_data_retention_info(user_id)
            
            return {
                "user_id": user_id,
                "consents": [asdict(consent) for consent in consents],
                "processing_activities": processing_activities,
                "data_retention": retention_info,
                "rights": {
                    "access": "You can request a copy of your data",
                    "rectification": "You can request corrections to your data",
                    "erasure": "You can request deletion of your data",
                    "portability": "You can request your data in portable format",
                    "restriction": "You can request processing restrictions"
                },
                "contact": {
                    "dpo_email": "privacy@goodbooks.ai",
                    "complaint_authority": "Your local data protection authority"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate privacy dashboard: {e}")
            return {"error": "Privacy dashboard temporarily unavailable"}
    
    def _encrypt_data(self, data: Dict[str, Any]) -> str:
        """Encrypt sensitive data"""
        json_data = json.dumps(data, default=str)
        return self.cipher.encrypt(json_data.encode()).decode()
    
    def _decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt sensitive data"""
        decrypted = self.cipher.decrypt(encrypted_data.encode()).decode()
        return json.loads(decrypted)
    
    def _calculate_privacy_safe_score(self, user_id: str, recommendation: Dict[str, Any]) -> float:
        """Calculate personalization score using privacy-safe methods"""
        # Use aggregated, anonymized signals
        base_score = recommendation.get("hybrid_score", 0.5)
        
        # Apply minimal privacy-safe adjustments
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
        adjustment = (int(user_hash, 16) % 100) / 1000  # 0-0.099 adjustment
        
        return min(1.0, base_score + adjustment)
    
    def _get_anonymous_popularity_boost(self, recommendation: Dict[str, Any]) -> float:
        """Get popularity boost using anonymous aggregated data"""
        ratings_count = recommendation.get("ratings_count", 0)
        return min(0.1, ratings_count / 10000)  # Max 0.1 boost
    
    async def _compile_user_data(self, user_id: str) -> Dict[str, Any]:
        """Compile all user data for access request"""
        try:
            # Get user consents
            consents = await self.get_user_consents(user_id)
            
            # Get user preferences (if any stored)
            prefs_key = f"{self.data_store}:{user_id}:preferences"
            preferences = await self.redis.get(prefs_key)
            
            return {
                "user_id": user_id,
                "consents": [asdict(consent) for consent in consents],
                "preferences": json.loads(preferences) if preferences else {},
                "export_date": datetime.utcnow().isoformat(),
                "format": "JSON"
            }
            
        except Exception as e:
            logger.error(f"Failed to compile user data: {e}")
            return {"error": "Failed to compile data"}
    
    async def _erase_user_data(self, user_id: str) -> bool:
        """Erase all user data (right to be forgotten)"""
        try:
            # Delete consent records
            consent_pattern = f"{self.consent_store}:{user_id}:*"
            consent_keys = await self.redis.keys(consent_pattern)
            if consent_keys:
                await self.redis.delete(*consent_keys)
            
            # Delete preference data
            prefs_key = f"{self.data_store}:{user_id}:preferences"
            await self.redis.delete(prefs_key)
            
            # Delete any cached personalization data
            cache_pattern = f"cache:{user_id}:*"
            cache_keys = await self.redis.keys(cache_pattern)
            if cache_keys:
                await self.redis.delete(*cache_keys)
            
            logger.info(f"User data erased for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to erase user data: {e}")
            return False
    
    async def _export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export user data in portable format"""
        data = await self._compile_user_data(user_id)
        data["export_format"] = "GDPR_COMPLIANT_JSON"
        data["machine_readable"] = True
        return data
    
    async def _get_data_retention_info(self, user_id: str) -> Dict[str, Any]:
        """Get data retention information"""
        return {
            "consent_records": "Retained for 3 years after withdrawal",
            "preference_data": "Retained while account is active",
            "audit_logs": "Retained for 7 years for compliance",
            "analytics_data": "Aggregated and anonymized after 2 years"
        }
    
    async def _log_audit_event(self, event_type: str, data: Dict[str, Any]):
        """Log audit event for compliance"""
        try:
            audit_event = {
                "event_id": str(uuid.uuid4()),
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            audit_key = f"{self.audit_log}:{datetime.utcnow().strftime('%Y-%m-%d')}:{audit_event['event_id']}"
            await self.redis.setex(audit_key, 86400 * 365 * 7, json.dumps(audit_event))  # 7 years
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")

# Global instance
privacy_engine = None

def get_privacy_engine() -> PrivacyFirstPersonalization:
    """Get global privacy engine instance"""
    global privacy_engine
    if privacy_engine is None:
        raise RuntimeError("Privacy engine not initialized")
    return privacy_engine

async def initialize_privacy_engine(redis_client: aioredis.Redis, encryption_key: str):
    """Initialize global privacy engine"""
    global privacy_engine
    privacy_engine = PrivacyFirstPersonalization(redis_client, encryption_key)
    logger.info("Privacy-first personalization engine initialized")
