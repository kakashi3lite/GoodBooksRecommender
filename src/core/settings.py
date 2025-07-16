"""
Production-grade configuration management using Pydantic BaseSettings.
Follows the bookworm instructions for configuration as code.
"""
import os
import secrets
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    url: str = Field("sqlite:///./goodbooks.db", env="DATABASE_URL")
    pool_size: int = Field(20, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(30, env="DATABASE_MAX_OVERFLOW")
    pool_timeout: int = Field(30, env="DATABASE_POOL_TIMEOUT")
    echo: bool = Field(False, env="DATABASE_ECHO")

    class Config:
        env_prefix = "DB_"


class RedisSettings(BaseSettings):
    """Redis configuration settings with cluster support."""
    # Single instance configuration
    host: str = Field("localhost", env="REDIS_HOST")
    port: int = Field(6379, env="REDIS_PORT")
    password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    db: int = Field(0, env="REDIS_DB")
    
    # Cluster configuration
    cluster_enabled: bool = Field(False, env="REDIS_CLUSTER_ENABLED")
    cluster_nodes: Optional[str] = Field(None, env="REDIS_CLUSTER_NODES")  # comma-separated host:port
    cluster_slots_refresh_interval: int = Field(10, env="REDIS_CLUSTER_SLOTS_REFRESH_INTERVAL")
    cluster_max_redirections: int = Field(3, env="REDIS_CLUSTER_MAX_REDIRECTIONS")
    cluster_retry_on_fail: bool = Field(True, env="REDIS_CLUSTER_RETRY_ON_FAIL")
    
    # Connection pooling
    pool_size: int = Field(50, env="REDIS_POOL_SIZE")
    pool_timeout: int = Field(5, env="REDIS_POOL_TIMEOUT")
    connection_timeout: int = Field(10, env="REDIS_CONNECTION_TIMEOUT")
    socket_timeout: int = Field(5, env="REDIS_SOCKET_TIMEOUT")
    
    # Security
    ssl: bool = Field(False, env="REDIS_SSL")
    ssl_cert_reqs: Optional[str] = Field(None, env="REDIS_SSL_CERT_REQS")
    ssl_ca_certs: Optional[str] = Field(None, env="REDIS_SSL_CA_CERTS")
    ssl_certfile: Optional[str] = Field(None, env="REDIS_SSL_CERTFILE")
    ssl_keyfile: Optional[str] = Field(None, env="REDIS_SSL_KEYFILE")
    
    # General settings
    decode_responses: bool = Field(True, env="REDIS_DECODE_RESPONSES")
    encoding: str = Field("utf-8", env="REDIS_ENCODING")
    
    # Health check
    health_check_interval: int = Field(30, env="REDIS_HEALTH_CHECK_INTERVAL")
    
    @validator("cluster_nodes", pre=True)
    def parse_cluster_nodes(cls, v):
        """Parse comma-separated cluster nodes into a list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [node.strip() for node in v.split(",") if node.strip()]
        return v
    
    @property
    def cluster_nodes_list(self) -> Optional[List[Dict[str, Any]]]:
        """Get cluster nodes as list of dictionaries."""
        if not self.cluster_nodes:
            return None
        
        nodes = []
        for node in self.cluster_nodes:
            if ":" in node:
                host, port = node.split(":", 1)
                nodes.append({"host": host, "port": int(port)})
            else:
                nodes.append({"host": node, "port": 6379})
        return nodes

    class Config:
        env_prefix = "REDIS_"


class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    # JWT Configuration
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(15, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # API Key Configuration
    default_api_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="DEFAULT_API_KEY")
    api_key_length: int = Field(32, env="API_KEY_LENGTH")
    api_keys: List[str] = Field([], env="API_KEYS")  # Additional API keys
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_day: int = Field(1000, env="RATE_LIMIT_PER_DAY")
    rate_limit_burst: int = Field(10, env="RATE_LIMIT_BURST")  # Burst limit
    
    # CORS and Host Configuration
    cors_origins: List[str] = Field(["*"], env="CORS_ORIGINS")
    allowed_hosts: List[str] = Field(["*"], env="ALLOWED_HOSTS")
    
    # Content Security Policy
    enable_csp: bool = Field(True, env="ENABLE_CSP")
    csp_policy: str = Field(
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;",
        env="CSP_POLICY"
    )
    
    # Security Headers
    enable_security_headers: bool = Field(True, env="ENABLE_SECURITY_HEADERS")
    hsts_max_age: int = Field(31536000, env="HSTS_MAX_AGE")  # 1 year
    
    # Data Privacy
    enable_data_anonymization: bool = Field(True, env="ENABLE_DATA_ANONYMIZATION")
    log_data_retention_days: int = Field(90, env="LOG_DATA_RETENTION_DAYS")
    session_data_retention_days: int = Field(90, env="SESSION_DATA_RETENTION_DAYS")
    
    # Encryption
    enable_data_encryption: bool = Field(True, env="ENABLE_DATA_ENCRYPTION")
    encryption_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="ENCRYPTION_KEY")
    
    # Input Validation
    max_request_size: int = Field(1048576, env="MAX_REQUEST_SIZE")  # 1MB
    max_query_params: int = Field(100, env="MAX_QUERY_PARAMS")
    max_headers: int = Field(100, env="MAX_HEADERS")
    
    # Authentication Settings
    password_min_length: int = Field(8, env="PASSWORD_MIN_LENGTH")
    password_require_uppercase: bool = Field(True, env="PASSWORD_REQUIRE_UPPERCASE")
    password_require_lowercase: bool = Field(True, env="PASSWORD_REQUIRE_LOWERCASE")
    password_require_numbers: bool = Field(True, env="PASSWORD_REQUIRE_NUMBERS")
    password_require_symbols: bool = Field(True, env="PASSWORD_REQUIRE_SYMBOLS")
    
    # Session Management
    session_timeout_minutes: int = Field(30, env="SESSION_TIMEOUT_MINUTES")
    max_sessions_per_user: int = Field(5, env="MAX_SESSIONS_PER_USER")
    
    # Role-Based Access Control
    enable_rbac: bool = Field(True, env="ENABLE_RBAC")
    default_user_role: str = Field("user", env="DEFAULT_USER_ROLE")
    admin_roles: List[str] = Field(["admin", "superuser"], env="ADMIN_ROLES")

    @validator("cors_origins", "allowed_hosts", "api_keys", "admin_roles", pre=True)
    def parse_comma_separated(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    class Config:
        env_prefix = "SECURITY_"


class MLSettings(BaseSettings):
    """Machine Learning model configuration."""
    content_weight: float = Field(0.5, env="CONTENT_WEIGHT", ge=0.0, le=1.0)
    n_factors: int = Field(50, env="N_FACTORS", gt=0)
    learning_rate: float = Field(0.01, env="LEARNING_RATE", gt=0.0, le=1.0)
    regularization: float = Field(0.02, env="REGULARIZATION", ge=0.0)
    n_epochs: int = Field(20, env="N_EPOCHS", gt=0)
    min_rating_threshold: float = Field(3.5, env="MIN_RATING_THRESHOLD", ge=1.0, le=5.0)
    default_num_recommendations: int = Field(5, env="DEFAULT_NUM_RECOMMENDATIONS", gt=0, le=50)
    max_recommendations: int = Field(50, env="MAX_RECOMMENDATIONS", gt=0)
    model_cache_ttl: int = Field(3600, env="MODEL_CACHE_TTL", gt=0)  # 1 hour

    class Config:
        env_prefix = "ML_"


class CacheSettings(BaseSettings):
    """Caching configuration."""
    ttl_default: int = Field(3600, env="CACHE_TTL_DEFAULT")  # 1 hour
    ttl_recommendations: int = Field(1800, env="CACHE_TTL_RECOMMENDATIONS")  # 30 minutes
    ttl_user_profile: int = Field(7200, env="CACHE_TTL_USER_PROFILE")  # 2 hours
    ttl_book_metadata: int = Field(86400, env="CACHE_TTL_BOOK_METADATA")  # 24 hours
    max_size: int = Field(10000, env="CACHE_MAX_SIZE")
    enable_cache_warming: bool = Field(True, env="CACHE_ENABLE_WARMING")

    class Config:
        env_prefix = "CACHE_"


class MonitoringSettings(BaseSettings):
    """Monitoring and observability settings."""
    prometheus_enabled: bool = Field(True, env="PROMETHEUS_ENABLED")
    metrics_path: str = Field("/metrics", env="METRICS_PATH")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    enable_request_logging: bool = Field(True, env="ENABLE_REQUEST_LOGGING")
    enable_performance_logging: bool = Field(True, env="ENABLE_PERFORMANCE_LOGGING")
    console_enabled: bool = Field(True, env="CONSOLE_LOGGING_ENABLED")

    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    # For backward compatibility
    @property
    def level(self):
        return self.log_level

    class Config:
        env_prefix = "MONITORING_"


class Settings(BaseSettings):
    """Main application settings."""
    
    # Environment
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    testing: bool = Field(False, env="TESTING")
    
    # Application
    app_name: str = Field("GoodBooks Recommender", env="APP_NAME")
    version: str = Field("2.0.0", env="APP_VERSION")
    description: str = Field(
        "Production-grade hybrid book recommendation system",
        env="APP_DESCRIPTION"
    )
    api_prefix: str = Field("/api/v1", env="API_PREFIX")
    
    # Server
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    workers: int = Field(4, env="WORKERS")
      # Nested settings
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    security: SecuritySettings = SecuritySettings()
    ml: MLSettings = MLSettings()
    cache: CacheSettings = CacheSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    
    # For backward compatibility - alias monitoring as logging
    @property
    def logging(self):
        return self.monitoring
      # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    models_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "models")
    logs_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "logs")
      # Data files
    books_file: str = Field("books.csv", env="BOOKS_FILE")
    ratings_file: str = Field("ratings.csv", env="RATINGS_FILE")
    tags_file: str = Field("tags.csv", env="TAGS_FILE")
    book_tags_file: str = Field("book_tags.csv", env="BOOK_TAGS_FILE")

    @validator("environment")
    def validate_environment(cls, v):
        valid_envs = ["development", "testing", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v.lower()

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_testing(self) -> bool:
        return self.environment == "testing" or self.testing
        return self.environment == "development"

    @property
    def data_paths(self) -> Dict[str, Path]:
        """Get paths to all data files."""
        return {
            "books": self.data_dir / self.books_file,
            "ratings": self.data_dir / self.ratings_file,
            "tags": self.data_dir / self.tags_file,
            "book_tags": self.data_dir / self.book_tags_file,
        }

    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [self.data_dir, self.models_dir, self.logs_dir]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.create_directories()
