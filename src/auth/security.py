"""
OAuth2 with JWT Token Authentication System
Implements secure authentication with role-based access control (RBAC)
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from enum import Enum

import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
from fastapi import HTTPException, Depends, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from pydantic import BaseModel, Field, validator
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from src.core.settings import settings
from src.core.enhanced_logging import StructuredLogger
from src.core.monitoring import MetricsCollector

logger = StructuredLogger(__name__)
metrics = MetricsCollector()

# Security scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
security = HTTPBearer()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, Enum):
    """User roles for RBAC."""
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPERUSER = "superuser"


class Permission(str, Enum):
    """Permissions for different operations."""
    # Read permissions
    READ_RECOMMENDATIONS = "read:recommendations"
    READ_BOOKS = "read:books"
    READ_USERS = "read:users"
    READ_ANALYTICS = "read:analytics"
    
    # Write permissions
    WRITE_RATINGS = "write:ratings"
    WRITE_REVIEWS = "write:reviews"
    
    # Admin permissions
    MANAGE_USERS = "manage:users"
    MANAGE_BOOKS = "manage:books"
    MANAGE_SYSTEM = "manage:system"
    
    # Analytics permissions
    VIEW_ANALYTICS = "view:analytics"
    EXPORT_DATA = "export:data"


# Role-Permission mapping
ROLE_PERMISSIONS = {
    UserRole.USER: [
        Permission.READ_RECOMMENDATIONS,
        Permission.READ_BOOKS,
        Permission.WRITE_RATINGS,
        Permission.WRITE_REVIEWS,
    ],
    UserRole.MODERATOR: [
        Permission.READ_RECOMMENDATIONS,
        Permission.READ_BOOKS,
        Permission.READ_USERS,
        Permission.WRITE_RATINGS,
        Permission.WRITE_REVIEWS,
        Permission.VIEW_ANALYTICS,
    ],
    UserRole.ADMIN: [
        Permission.READ_RECOMMENDATIONS,
        Permission.READ_BOOKS,
        Permission.READ_USERS,
        Permission.READ_ANALYTICS,
        Permission.WRITE_RATINGS,
        Permission.WRITE_REVIEWS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_BOOKS,
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_DATA,
    ],
    UserRole.SUPERUSER: [perm for perm in Permission],  # All permissions
}


class TokenData(BaseModel):
    """Token payload data."""
    user_id: int
    username: str
    email: str
    role: UserRole
    permissions: List[Permission]
    session_id: str
    exp: datetime
    iat: datetime
    token_type: str = "access"


class User(BaseModel):
    """User model for authentication."""
    id: int
    username: str
    email: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """User creation model."""
    username: str = Field(..., min_length=3, max_length=50, regex=r"^[a-zA-Z0-9_-]+$")
    email: str = Field(..., regex=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.USER
    
    @validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < settings.security.password_min_length:
            raise ValueError(f"Password must be at least {settings.security.password_min_length} characters")
        
        if settings.security.password_require_uppercase and not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if settings.security.password_require_lowercase and not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if settings.security.password_require_numbers and not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        
        if settings.security.password_require_symbols and not any(c in "!@#$%^&*(),.?\":{}|<>" for c in v):
            raise ValueError("Password must contain at least one symbol")
        
        return v


class UserLogin(BaseModel):
    """User login model."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: User


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: str


class PasswordReset(BaseModel):
    """Password reset model."""
    token: str
    new_password: str
    
    @validator("new_password")
    def validate_password(cls, v):
        """Validate password strength."""
        return UserCreate.__validators__["validate_password"](v)


class SecurityService:
    """Security service for authentication and authorization."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.secret_key = settings.security.secret_key
        self.algorithm = settings.security.jwt_algorithm
        self.access_token_expire_minutes = settings.security.access_token_expire_minutes
        self.refresh_token_expire_days = settings.security.refresh_token_expire_days
        
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token."""
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        session_id = secrets.token_urlsafe(16)
        
        # Get user permissions
        permissions = ROLE_PERMISSIONS.get(user.role, [])
        
        payload = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "permissions": [perm.value for perm in permissions],
            "session_id": session_id,
            "exp": expire,
            "iat": now,
            "token_type": "access"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        # Store session in Redis
        asyncio.create_task(self._store_session(session_id, user.id, expire))
        
        return token
    
    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token."""
        now = datetime.utcnow()
        expire = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "user_id": user.id,
            "exp": expire,
            "iat": now,
            "token_type": "refresh"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    async def _store_session(self, session_id: str, user_id: int, expire: datetime) -> None:
        """Store session in Redis."""
        try:
            ttl = int((expire - datetime.utcnow()).total_seconds())
            await self.redis.setex(f"session:{session_id}", ttl, str(user_id))
            
            # Track active sessions for user
            await self.redis.sadd(f"user_sessions:{user_id}", session_id)
            await self.redis.expire(f"user_sessions:{user_id}", ttl)
            
        except Exception as e:
            logger.error("Failed to store session", session_id=session_id, user_id=user_id, error=str(e))
    
    async def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if session is still valid
            session_id = payload.get("session_id")
            if session_id:
                session_valid = await self.redis.exists(f"session:{session_id}")
                if not session_valid:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Session expired or invalid"
                    )
            
            return TokenData(**payload)
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.JWTError as e:
            logger.warning("Invalid token", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    async def refresh_access_token(self, refresh_token: str) -> str:
        """Refresh access token using refresh token."""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("token_type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Get user from database (you'll need to implement this)
            # user = await get_user_by_id(user_id)
            # For now, create a mock user
            user = User(
                id=user_id,
                username="user",
                email="user@example.com",
                role=UserRole.USER,
                created_at=datetime.utcnow()
            )
            
            return self.create_access_token(user)
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    
    async def revoke_session(self, session_id: str, user_id: int) -> None:
        """Revoke a user session."""
        try:
            await self.redis.delete(f"session:{session_id}")
            await self.redis.srem(f"user_sessions:{user_id}", session_id)
            
            logger.info("Session revoked", session_id=session_id, user_id=user_id)
            
        except Exception as e:
            logger.error("Failed to revoke session", session_id=session_id, error=str(e))
    
    async def revoke_all_user_sessions(self, user_id: int) -> None:
        """Revoke all sessions for a user."""
        try:
            session_ids = await self.redis.smembers(f"user_sessions:{user_id}")
            
            if session_ids:
                # Delete all session keys
                session_keys = [f"session:{sid}" for sid in session_ids]
                await self.redis.delete(*session_keys)
                
                # Clear user sessions set
                await self.redis.delete(f"user_sessions:{user_id}")
                
                logger.info("All user sessions revoked", user_id=user_id, count=len(session_ids))
            
        except Exception as e:
            logger.error("Failed to revoke user sessions", user_id=user_id, error=str(e))
    
    def generate_password_reset_token(self, email: str) -> str:
        """Generate password reset token."""
        now = datetime.utcnow()
        expire = now + timedelta(hours=1)  # Reset token expires in 1 hour
        
        payload = {
            "email": email,
            "exp": expire,
            "iat": now,
            "token_type": "password_reset"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    async def verify_password_reset_token(self, token: str) -> str:
        """Verify password reset token and return email."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("token_type") != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type"
                )
            
            return payload.get("email")
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password reset token"
            )


class RBACService:
    """Role-Based Access Control service."""
    
    @staticmethod
    def has_permission(user_role: UserRole, required_permission: Permission) -> bool:
        """Check if user role has required permission."""
        user_permissions = ROLE_PERMISSIONS.get(user_role, [])
        return required_permission in user_permissions
    
    @staticmethod
    def has_any_permission(user_role: UserRole, required_permissions: List[Permission]) -> bool:
        """Check if user role has any of the required permissions."""
        user_permissions = ROLE_PERMISSIONS.get(user_role, [])
        return any(perm in user_permissions for perm in required_permissions)
    
    @staticmethod
    def has_all_permissions(user_role: UserRole, required_permissions: List[Permission]) -> bool:
        """Check if user role has all required permissions."""
        user_permissions = ROLE_PERMISSIONS.get(user_role, [])
        return all(perm in user_permissions for perm in required_permissions)
    
    @staticmethod
    def is_admin(user_role: UserRole) -> bool:
        """Check if user has admin privileges."""
        return user_role in [UserRole.ADMIN, UserRole.SUPERUSER]
    
    @staticmethod
    def can_access_resource(user_role: UserRole, resource_owner_id: int, current_user_id: int) -> bool:
        """Check if user can access a resource (own resource or admin)."""
        return resource_owner_id == current_user_id or RBACService.is_admin(user_role)


# Global security service instance
_security_service: Optional[SecurityService] = None

def get_security_service() -> SecurityService:
    """Get or create security service instance."""
    global _security_service
    if _security_service is None:
        # You'll need to initialize Redis client here
        # redis_client = get_redis_client()
        # _security_service = SecurityService(redis_client)
        pass
    return _security_service


# Dependency functions for FastAPI
async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Get current authenticated user."""
    security_service = get_security_service()
    token_data = await security_service.verify_token(token)
    
    # Track authentication metric
    metrics.track_authentication_success()
    
    logger.info("User authenticated", user_id=token_data.user_id, username=token_data.username)
    
    return token_data


async def get_current_active_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Get current active user (additional checks can be added here)."""
    return current_user


def require_permission(permission: Permission):
    """Decorator to require specific permission."""
    def permission_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if not RBACService.has_permission(current_user.role, permission):
            logger.warning(
                "Permission denied",
                user_id=current_user.user_id,
                required_permission=permission.value,
                user_role=current_user.role.value
            )
            metrics.track_authorization_failure(permission.value)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {permission.value}"
            )
        
        metrics.track_authorization_success(permission.value)
        return current_user
    
    return permission_checker


def require_role(required_role: UserRole):
    """Decorator to require specific role or higher."""
    def role_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.MODERATOR: 2,
            UserRole.ADMIN: 3,
            UserRole.SUPERUSER: 4
        }
        
        if role_hierarchy.get(current_user.role, 0) < role_hierarchy.get(required_role, 0):
            logger.warning(
                "Role requirement not met",
                user_id=current_user.user_id,
                required_role=required_role.value,
                user_role=current_user.role.value
            )
            metrics.track_authorization_failure(f"role:{required_role.value}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role requirement not met. Required: {required_role.value}"
            )
        
        return current_user
    
    return role_checker


def require_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require admin role."""
    if not RBACService.is_admin(current_user.role):
        logger.warning(
            "Admin access denied",
            user_id=current_user.user_id,
            user_role=current_user.role.value
        )
        metrics.track_authorization_failure("admin")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


# API Key authentication (for backwards compatibility)
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Verify API key authentication."""
    api_key = credentials.credentials
    
    # Check if API key is valid
    valid_keys = [settings.security.default_api_key] + settings.security.api_keys
    
    if api_key not in valid_keys:
        logger.warning("Invalid API key", api_key_prefix=api_key[:8] if api_key else "none")
        metrics.track_authentication_failure("api_key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    metrics.track_authentication_success("api_key")
    return api_key
