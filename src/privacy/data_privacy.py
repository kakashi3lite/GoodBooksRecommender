"""
Data Privacy Service
Handles data anonymization, encryption, and retention policies for GDPR compliance.
"""

import re
import hashlib
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from enum import Enum

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import redis.asyncio as redis
import base64
import secrets

from src.core.settings import settings
from src.core.enhanced_logging import StructuredLogger
from src.core.monitoring import MetricsCollector

logger = StructuredLogger(__name__)
metrics = MetricsCollector()


class DataClassification(str, Enum):
    """Data classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class PIIType(str, Enum):
    """Types of Personally Identifiable Information."""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    USER_ID = "user_id"
    NAME = "name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"


class RetentionPolicy:
    """Data retention policy configuration."""
    
    def __init__(
        self,
        data_type: str,
        retention_days: int,
        auto_delete: bool = True,
        archive_before_delete: bool = True,
        classification: DataClassification = DataClassification.INTERNAL
    ):
        self.data_type = data_type
        self.retention_days = retention_days
        self.auto_delete = auto_delete
        self.archive_before_delete = archive_before_delete
        self.classification = classification
        self.created_at = datetime.utcnow()


class DataPrivacyService:
    """Service for handling data privacy, anonymization, and retention."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.encryption_key = self._derive_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # PII detection patterns
        self.pii_patterns = {
            PIIType.EMAIL: re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                re.IGNORECASE
            ),
            PIIType.PHONE: re.compile(
                r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
                re.IGNORECASE
            ),
            PIIType.SSN: re.compile(
                r'\b\d{3}-?\d{2}-?\d{4}\b'
            ),
            PIIType.CREDIT_CARD: re.compile(
                r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
            ),
            PIIType.IP_ADDRESS: re.compile(
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            ),
        }
        
        # Retention policies
        self.retention_policies = {
            "user_sessions": RetentionPolicy("user_sessions", settings.security.session_data_retention_days),
            "audit_logs": RetentionPolicy("audit_logs", settings.security.log_data_retention_days),
            "api_logs": RetentionPolicy("api_logs", 30),
            "error_logs": RetentionPolicy("error_logs", 90),
            "user_data": RetentionPolicy("user_data", 365 * 2, auto_delete=False),  # 2 years, manual review
            "recommendation_history": RetentionPolicy("recommendation_history", 365),  # 1 year
            "analytics_data": RetentionPolicy("analytics_data", 365 * 3),  # 3 years
        }
    
    def _derive_encryption_key(self) -> bytes:
        """Derive encryption key from settings."""
        password = settings.security.encryption_key.encode()
        salt = b'goodbooks_salt_2024'  # In production, use a secure random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def detect_pii(self, text: str) -> Dict[PIIType, List[str]]:
        """Detect PII in text and return matches."""
        detected_pii = {}
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected_pii[pii_type] = matches
        
        return detected_pii
    
    def anonymize_text(self, text: str, preserve_format: bool = True) -> str:
        """Anonymize PII in text."""
        if not settings.security.enable_data_anonymization:
            return text
        
        anonymized = text
        
        for pii_type, pattern in self.pii_patterns.items():
            if preserve_format:
                # Replace with format-preserving anonymization
                if pii_type == PIIType.EMAIL:
                    anonymized = pattern.sub(self._anonymize_email, anonymized)
                elif pii_type == PIIType.PHONE:
                    anonymized = pattern.sub(self._anonymize_phone, anonymized)
                elif pii_type == PIIType.CREDIT_CARD:
                    anonymized = pattern.sub(self._anonymize_credit_card, anonymized)
                elif pii_type == PIIType.IP_ADDRESS:
                    anonymized = pattern.sub(self._anonymize_ip_address, anonymized)
                else:
                    anonymized = pattern.sub(f"[{pii_type.value.upper()}_ANONYMIZED]", anonymized)
            else:
                anonymized = pattern.sub(f"[{pii_type.value.upper()}_ANONYMIZED]", anonymized)
        
        return anonymized
    
    def _anonymize_email(self, match) -> str:
        """Anonymize email while preserving format."""
        email = match.group(0)
        if '@' in email:
            local, domain = email.split('@', 1)
            # Keep first and last character of local part
            if len(local) > 2:
                local = local[0] + '*' * (len(local) - 2) + local[-1]
            elif len(local) == 2:
                local = local[0] + '*'
            else:
                local = '*'
            return f"{local}@{domain}"
        return "[EMAIL_ANONYMIZED]"
    
    def _anonymize_phone(self, match) -> str:
        """Anonymize phone number while preserving format."""
        phone = match.group(0)
        # Keep area code, anonymize rest
        if len(phone) >= 10:
            return phone[:3] + '*' * (len(phone) - 6) + phone[-3:]
        return "[PHONE_ANONYMIZED]"
    
    def _anonymize_credit_card(self, match) -> str:
        """Anonymize credit card while preserving last 4 digits."""
        card = match.group(0)
        # Keep last 4 digits
        cleaned = re.sub(r'[-\s]', '', card)
        if len(cleaned) >= 4:
            return '*' * (len(cleaned) - 4) + cleaned[-4:]
        return "[CARD_ANONYMIZED]"
    
    def _anonymize_ip_address(self, match) -> str:
        """Anonymize IP address while preserving network."""
        ip = match.group(0)
        parts = ip.split('.')
        if len(parts) == 4:
            # Keep first two octets, anonymize last two
            return f"{parts[0]}.{parts[1]}.xxx.xxx"
        return "[IP_ANONYMIZED]"
    
    def create_pseudonym(self, original_value: str, salt: Optional[str] = None) -> str:
        """Create a consistent pseudonym for a value."""
        if salt is None:
            salt = settings.security.secret_key
        
        # Create a hash-based pseudonym
        combined = f"{original_value}{salt}"
        hash_value = hashlib.sha256(combined.encode()).hexdigest()
        return f"pseudo_{hash_value[:16]}"
    
    def encrypt_sensitive_data(self, data: Any) -> str:
        """Encrypt sensitive data."""
        if not settings.security.enable_data_encryption:
            return str(data)
        
        try:
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, default=str)
            else:
                data_str = str(data)
            
            encrypted = self.cipher.encrypt(data_str.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        
        except Exception as e:
            logger.error("Encryption failed", error=str(e))
            metrics.track_security_incident("encryption_failure")
            return str(data)
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not settings.security.enable_data_encryption:
            return encrypted_data
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        
        except Exception as e:
            logger.error("Decryption failed", error=str(e))
            metrics.track_security_incident("decryption_failure")
            return encrypted_data
    
    def mask_sensitive_fields(self, data: Dict[str, Any], sensitive_fields: Set[str]) -> Dict[str, Any]:
        """Mask sensitive fields in a dictionary."""
        masked_data = data.copy()
        
        for field in sensitive_fields:
            if field in masked_data:
                value = masked_data[field]
                if isinstance(value, str) and value:
                    if len(value) <= 4:
                        masked_data[field] = '*' * len(value)
                    else:
                        masked_data[field] = value[:2] + '*' * (len(value) - 4) + value[-2:]
                else:
                    masked_data[field] = '[MASKED]'
        
        return masked_data
    
    async def apply_retention_policy(self, data_type: str) -> Dict[str, int]:
        """Apply retention policy for a specific data type."""
        policy = self.retention_policies.get(data_type)
        if not policy:
            logger.warning("No retention policy found", data_type=data_type)
            return {"deleted": 0, "archived": 0}
        
        cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)
        
        try:
            # Get expired data keys
            pattern = f"{data_type}:*"
            keys = await self.redis.keys(pattern)
            
            deleted_count = 0
            archived_count = 0
            
            for key in keys:
                # Check if data is expired (this is simplified - in practice,
                # you'd need to check actual timestamps)
                key_info = await self.redis.hgetall(f"{key}:metadata")
                if not key_info:
                    continue
                
                created_at_str = key_info.get('created_at')
                if not created_at_str:
                    continue
                
                created_at = datetime.fromisoformat(created_at_str)
                
                if created_at < cutoff_date:
                    if policy.archive_before_delete:
                        # Archive data before deletion
                        await self._archive_data(key, data_type)
                        archived_count += 1
                    
                    if policy.auto_delete:
                        await self.redis.delete(key)
                        await self.redis.delete(f"{key}:metadata")
                        deleted_count += 1
                        
                        logger.info(
                            "Data deleted per retention policy",
                            data_type=data_type,
                            key=key,
                            retention_days=policy.retention_days
                        )
            
            metrics.track_data_retention_cleanup(data_type, deleted_count, archived_count)
            
            return {"deleted": deleted_count, "archived": archived_count}
        
        except Exception as e:
            logger.error("Retention policy application failed", data_type=data_type, error=str(e))
            return {"deleted": 0, "archived": 0}
    
    async def _archive_data(self, key: str, data_type: str) -> None:
        """Archive data before deletion."""
        try:
            # Get data
            data = await self.redis.hgetall(key)
            if not data:
                return
            
            # Create archive record
            archive_key = f"archive:{data_type}:{datetime.utcnow().isoformat()}:{key}"
            archive_data = {
                "original_key": key,
                "data_type": data_type,
                "archived_at": datetime.utcnow().isoformat(),
                "data": json.dumps(data, default=str)
            }
            
            # Store in archive (you might want to use a different storage backend)
            await self.redis.hset(archive_key, mapping=archive_data)
            
            # Set long expiration for archives (e.g., 7 years for compliance)
            await self.redis.expire(archive_key, 365 * 7 * 24 * 3600)
            
            logger.info("Data archived", key=key, archive_key=archive_key)
        
        except Exception as e:
            logger.error("Data archiving failed", key=key, error=str(e))
    
    async def run_retention_cleanup(self) -> Dict[str, Dict[str, int]]:
        """Run retention cleanup for all data types."""
        results = {}
        
        for data_type in self.retention_policies:
            try:
                result = await self.apply_retention_policy(data_type)
                results[data_type] = result
                
                logger.info(
                    "Retention cleanup completed",
                    data_type=data_type,
                    deleted=result["deleted"],
                    archived=result["archived"]
                )
            
            except Exception as e:
                logger.error("Retention cleanup failed", data_type=data_type, error=str(e))
                results[data_type] = {"deleted": 0, "archived": 0, "error": str(e)}
        
        return results
    
    def audit_data_usage(self, user_id: int, data_accessed: str, purpose: str) -> None:
        """Audit data usage for compliance."""
        audit_record = {
            "user_id": user_id,
            "data_accessed": data_accessed,
            "purpose": purpose,
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": "[ANONYMIZED]",  # Would be filled by middleware
        }
        
        logger.info(
            "Data access audit",
            **audit_record
        )
        
        # Store audit record (implement based on your audit storage needs)
        asyncio.create_task(self._store_audit_record(audit_record))
    
    async def _store_audit_record(self, audit_record: Dict[str, Any]) -> None:
        """Store audit record."""
        try:
            audit_key = f"audit:{datetime.utcnow().date()}:{secrets.token_hex(8)}"
            await self.redis.hset(audit_key, mapping=audit_record)
            
            # Set expiration based on audit log retention policy
            policy = self.retention_policies.get("audit_logs")
            if policy:
                await self.redis.expire(audit_key, policy.retention_days * 24 * 3600)
        
        except Exception as e:
            logger.error("Failed to store audit record", error=str(e))
    
    def get_privacy_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get privacy summary of data."""
        pii_detected = {}
        
        # Check all string values for PII
        for key, value in data.items():
            if isinstance(value, str):
                detected = self.detect_pii(value)
                if detected:
                    pii_detected[key] = list(detected.keys())
        
        return {
            "pii_fields": pii_detected,
            "total_pii_types": len(set().union(*pii_detected.values())) if pii_detected else 0,
            "requires_anonymization": len(pii_detected) > 0,
            "data_classification": self._classify_data(pii_detected)
        }
    
    def _classify_data(self, pii_detected: Dict[str, List[PIIType]]) -> DataClassification:
        """Classify data based on PII content."""
        if not pii_detected:
            return DataClassification.PUBLIC
        
        sensitive_pii = {PIIType.SSN, PIIType.CREDIT_CARD}
        
        for field_pii in pii_detected.values():
            if any(pii in sensitive_pii for pii in field_pii):
                return DataClassification.RESTRICTED
        
        return DataClassification.CONFIDENTIAL


class ConsentManager:
    """Manage user consent for data processing."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def record_consent(
        self,
        user_id: int,
        consent_type: str,
        granted: bool,
        purpose: str,
        legal_basis: str = "consent"
    ) -> None:
        """Record user consent."""
        consent_record = {
            "user_id": user_id,
            "consent_type": consent_type,
            "granted": granted,
            "purpose": purpose,
            "legal_basis": legal_basis,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0"  # Consent version for tracking changes
        }
        
        consent_key = f"consent:{user_id}:{consent_type}"
        await self.redis.hset(consent_key, mapping=consent_record)
        
        logger.info(
            "Consent recorded",
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            purpose=purpose
        )
    
    async def check_consent(self, user_id: int, consent_type: str) -> bool:
        """Check if user has granted consent."""
        consent_key = f"consent:{user_id}:{consent_type}"
        consent_record = await self.redis.hgetall(consent_key)
        
        if not consent_record:
            return False
        
        return consent_record.get("granted", "false").lower() == "true"
    
    async def withdraw_consent(self, user_id: int, consent_type: str) -> None:
        """Withdraw user consent."""
        await self.record_consent(user_id, consent_type, False, "consent_withdrawn")
        
        logger.info(
            "Consent withdrawn",
            user_id=user_id,
            consent_type=consent_type
        )
    
    async def get_user_consents(self, user_id: int) -> Dict[str, Dict[str, Any]]:
        """Get all consents for a user."""
        pattern = f"consent:{user_id}:*"
        keys = await self.redis.keys(pattern)
        
        consents = {}
        for key in keys:
            consent_type = key.split(":")[-1]
            consent_data = await self.redis.hgetall(key)
            consents[consent_type] = consent_data
        
        return consents


# Global instances
_privacy_service: Optional[DataPrivacyService] = None
_consent_manager: Optional[ConsentManager] = None

def get_privacy_service() -> DataPrivacyService:
    """Get privacy service instance."""
    global _privacy_service
    if _privacy_service is None:
        # Initialize with Redis client - you'll need to implement this
        # redis_client = get_redis_client()
        # _privacy_service = DataPrivacyService(redis_client)
        pass
    return _privacy_service

def get_consent_manager() -> ConsentManager:
    """Get consent manager instance."""
    global _consent_manager
    if _consent_manager is None:
        # Initialize with Redis client - you'll need to implement this
        # redis_client = get_redis_client()
        # _consent_manager = ConsentManager(redis_client)
        pass
    return _consent_manager
