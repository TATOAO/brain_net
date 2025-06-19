"""
Configuration settings for Brain_Net Backend
Loads configuration from environment variables with proper validation.
"""

import os
from typing import List, Optional
from datetime import datetime
from pydantic import field_validator
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
    
    # Document Processing Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB in bytes
    SUPPORTED_FORMATS: List[str] = ["pdf", "docx", "txt", "md", "html", "csv", "json"]
    
    # Query Generation Settings
    QUERY_GENERATION_MODEL: str = "gpt-3.5-turbo"
    QUERIES_PER_DOCUMENT: int = 5
    QUERY_COMPLEXITY_LEVELS: List[str] = ["simple", "medium", "complex"]
    
    # Security Settings
    SECRET_KEY: str = "your_secret_key_here_minimum_32_characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:80"]
    CORS_METHODS: str = "GET,POST,PUT,DELETE,OPTIONS"
    CORS_HEADERS: str = "*"
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = True
    METRICS_PORT: int = 8080
    
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
        "case_sensitive": True
    }
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("SUPPORTED_FORMATS", mode="before")
    @classmethod
    def parse_supported_formats(cls, v):
        """Parse supported formats from comma-separated string."""
        if isinstance(v, str):
            return [fmt.strip() for fmt in v.split(",")]
        return v
    
    @field_validator("QUERY_COMPLEXITY_LEVELS", mode="before")
    @classmethod
    def parse_complexity_levels(cls, v):
        """Parse query complexity levels from comma-separated string."""
        if isinstance(v, str):
            return [level.strip() for level in v.split(",")]
        return v
    
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
settings = get_settings() 