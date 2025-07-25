"""
Configuration settings for Brain_Net Backend
Loads configuration from environment variables with proper validation.
"""

import os
from typing import List, Optional, Union
from datetime import datetime
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Settings
    APP_NAME: str = "Brain_Net"
    APP_VERSION: str = "1.0.0"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_DEBUG: bool = True
    BACKEND_RELOAD: bool = True
    
    # Database Settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/brain_net"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Elasticsearch Settings
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX_PREFIX: str = "brain_net"
    ELASTICSEARCH_TIMEOUT: int = 30
    
    # Neo4j Settings
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "neo4j"
    
    # MinIO Settings
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "brain-net-documents"
    MINIO_SECURE: bool = False
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_TIMEOUT: int = 5
    
    # AI/ML Settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    HUGGINGFACE_API_TOKEN: Optional[str] = None
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 2048
    
    # LLM Service Settings
    LLM_SERVICE_URL: str = "http://llm:8001"
    
    # Document Processing Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB in bytes
    SUPPORTED_FORMATS: Union[str, List[str]] = Field(default="pdf,docx,txt,md,html,csv,json")
    
    # Query Generation Settings
    QUERY_GENERATION_MODEL: str = "gpt-3.5-turbo"
    QUERIES_PER_DOCUMENT: int = 5
    QUERY_COMPLEXITY_LEVELS: Union[str, List[str]] = Field(default="simple,medium,complex")
    
    # Security Settings
    SECRET_KEY: str = "your_secret_key_here_minimum_32_characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS Settings
    CORS_ORIGINS: Union[str, List[str]] = Field(default="http://localhost:3000,http://localhost:80")
    CORS_METHODS: str = "GET,POST,PUT,DELETE,OPTIONS"
    CORS_HEADERS: str = "*"
    
    # Service Dependencies Settings
    REQUIRED_SERVICES: Union[str, List[str]] = Field(default="postgres")  # Services that MUST be available
    OPTIONAL_SERVICES: Union[str, List[str]] = Field(default="elasticsearch,neo4j,minio,redis")  # Services that are nice-to-have
    ENABLE_GRACEFUL_DEGRADATION: bool = True  # Allow app to start with some services unavailable
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = True
    METRICS_PORT: int = 8080
    
    # OpenTelemetry Settings
    OTEL_ENABLED: bool = Field(default=True, env="OTEL_ENABLED")
    OTEL_REQUIRED: bool = Field(default=False, env="OTEL_REQUIRED")
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(default="http://otel-collector:4317", env="OTEL_EXPORTER_OTLP_ENDPOINT")
    OTEL_SERVICE_NAME: str = Field(default="brain_net_backend", env="OTEL_SERVICE_NAME")
    OTEL_SERVICE_VERSION: str = Field(default="1.0.0", env="OTEL_SERVICE_VERSION")
    OTEL_RESOURCE_ATTRIBUTES: str = Field(default="", env="OTEL_RESOURCE_ATTRIBUTES")
    OTEL_INSECURE: bool = Field(default=True, env="OTEL_INSECURE")

    # Compact LLM Settings
    COMPACT_LLM_URL: str = "http://localhost:8000"
    
    # Health Check Settings
    HEALTH_CHECK_INTERVAL: str = "30s"
    HEALTH_CHECK_TIMEOUT: str = "10s"
    HEALTH_CHECK_RETRIES: int = 3
    
    # Development Settings
    DEV_MODE: bool = True
    HOT_RELOAD: bool = True
    DEBUG_SQL: bool = False
    DEBUG_ELASTICSEARCH: bool = False
    MOCK_AI_RESPONSES: bool = False
    
    # Testing Settings
    TEST_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/brain_net_test"
    TEST_ELASTICSEARCH_URL: str = "http://localhost:9200"
    TEST_REDIS_URL: str = "redis://localhost:6379/1"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "env_parse_none_str": "None",
        "env_parse_enums": True,
        "env_nested_delimiter": "__",
        "env_ignore_empty": True
    }
    
    @field_validator("CORS_ORIGINS", "REQUIRED_SERVICES", "OPTIONAL_SERVICES", "SUPPORTED_FORMATS", "QUERY_COMPLEXITY_LEVELS")
    @classmethod
    def parse_list_fields(cls, v, info):
        """Parse list fields from comma-separated string or return list as-is."""
        field_name = info.field_name
        
        # Default values for each field  
        defaults = {
            "CORS_ORIGINS": ["http://localhost:3000", "http://localhost:80"],
            "REQUIRED_SERVICES": ["postgres"],
            "OPTIONAL_SERVICES": ["elasticsearch", "neo4j", "minio", "redis"],
            "SUPPORTED_FORMATS": ["pdf", "docx", "txt", "md", "html", "csv", "json"],
            "QUERY_COMPLEXITY_LEVELS": ["simple", "medium", "complex"]
        }
        
        if isinstance(v, str) and v.strip():
            return [item.strip() for item in v.split(",") if item.strip()]
        elif isinstance(v, list):
            return v
        else:
            return defaults.get(field_name, [])
    
    @field_validator("MAX_FILE_SIZE", mode="before")
    @classmethod
    def parse_max_file_size(cls, v):
        """Convert max file size to bytes."""
        if isinstance(v, str):
            v = v.upper()
            if v.endswith("MB"):
                return int(v[:-2]) * 1024 * 1024
            elif v.endswith("KB"):
                return int(v[:-2]) * 1024
            elif v.endswith("GB"):
                return int(v[:-2]) * 1024 * 1024 * 1024
            else:
                return int(v)
        return v
    
    def get_database_url(self, async_driver: bool = True) -> str:
        """Get database URL with optional async driver."""
        if async_driver and not self.DATABASE_URL.startswith("postgresql+asyncpg://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        return self.DATABASE_URL
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat() + "Z"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.DEV_MODE and self.BACKEND_DEBUG
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return "test" in self.DATABASE_URL.lower()


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
# Note: This will be initialized when first accessed to prevent import-time errors
_settings = None

def get_settings_instance():
    """Get the global settings instance, creating it if necessary."""
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings

# Create a lazy settings proxy
class SettingsProxy:
    def __init__(self):
        self._settings = None
    
    def __getattr__(self, name):
        if self._settings is None:
            self._settings = get_settings()
        return getattr(self._settings, name)

# For backwards compatibility
settings = SettingsProxy() 