"""
Configuration settings for Brain_Net LLM Service
"""

import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings for LLM Service."""
    
    # Basic App Settings
    APP_NAME: str = "Brain_Net LLM Service"
    DEBUG: bool = Field(default=False, env="LLM_DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    # Database Settings (shared with backend)
    DATABASE_URL: str = Field(env="DATABASE_URL")
    ELASTICSEARCH_URL: str = Field(default="http://localhost:9200", env="ELASTICSEARCH_URL")
    NEO4J_URI: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    NEO4J_USER: str = Field(default="neo4j", env="NEO4J_USER")
    NEO4J_PASSWORD: str = Field(default="password", env="NEO4J_PASSWORD")
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    MINIO_ENDPOINT: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", env="MINIO_SECRET_KEY")
    
    # LLM Provider Settings
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    HUGGINGFACE_API_KEY: Optional[str] = Field(default=None, env="HUGGINGFACE_API_KEY")
    
    # Model Settings
    DEFAULT_LLM_MODEL: str = Field(default="gpt-3.5-turbo", env="DEFAULT_LLM_MODEL")
    DEFAULT_EMBEDDING_MODEL: str = Field(default="text-embedding-ada-002", env="DEFAULT_EMBEDDING_MODEL")
    LOCAL_MODEL_PATH: Optional[str] = Field(default=None, env="LOCAL_MODEL_PATH")
    
    # Vector Store Settings
    VECTOR_STORE_TYPE: str = Field(default="elasticsearch", env="VECTOR_STORE_TYPE")  # elasticsearch, chroma, pinecone
    VECTOR_DIMENSION: int = Field(default=1536, env="VECTOR_DIMENSION")
    SIMILARITY_THRESHOLD: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    MAX_SEARCH_RESULTS: int = Field(default=10, env="MAX_SEARCH_RESULTS")
    
    # RAG Settings
    CHUNK_SIZE: int = Field(default=1000, env="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(default=200, env="CHUNK_OVERLAP")
    MAX_CONTEXT_LENGTH: int = Field(default=4000, env="MAX_CONTEXT_LENGTH")
    
    # Agent Settings
    CREWAI_ENABLED: bool = Field(default=True, env="CREWAI_ENABLED")
    LANGRAPH_ENABLED: bool = Field(default=True, env="LANGRAPH_ENABLED")
    MAX_AGENT_ITERATIONS: int = Field(default=10, env="MAX_AGENT_ITERATIONS")
    AGENT_TIMEOUT: int = Field(default=300, env="AGENT_TIMEOUT")  # seconds
    
    # Performance Settings
    MAX_CONCURRENT_REQUESTS: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    MODEL_CACHE_SIZE: int = Field(default=3, env="MODEL_CACHE_SIZE")
    EMBEDDING_BATCH_SIZE: int = Field(default=100, env="EMBEDDING_BATCH_SIZE")
    
    # Service Dependencies
    REQUIRED_SERVICES: List[str] = Field(
        default=["postgres", "redis"],
        env="REQUIRED_SERVICES"
    )
    OPTIONAL_SERVICES: List[str] = Field(
        default=["elasticsearch", "neo4j", "minio"],
        env="OPTIONAL_SERVICES"
    )
    
    # OpenTelemetry Settings
    OTEL_ENABLED: bool = Field(default=True, env="OTEL_ENABLED")
    OTEL_REQUIRED: bool = Field(default=False, env="OTEL_REQUIRED")
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(default="http://otel-collector:4317", env="OTEL_EXPORTER_OTLP_ENDPOINT")
    OTEL_SERVICE_NAME: str = Field(default="brain_net_llm", env="OTEL_SERVICE_NAME")
    OTEL_SERVICE_VERSION: str = Field(default="1.0.0", env="OTEL_SERVICE_VERSION")
    OTEL_RESOURCE_ATTRIBUTES: str = Field(default="", env="OTEL_RESOURCE_ATTRIBUTES")
    OTEL_INSECURE: bool = Field(default=True, env="OTEL_INSECURE")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @staticmethod
    def get_current_timestamp() -> str:
        """Get current timestamp as ISO string."""
        return datetime.utcnow().isoformat()
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get configuration for a specific model."""
        configs = {
            "gpt-3.5-turbo": {
                "provider": "openai",
                "max_tokens": 4096,
                "temperature": 0.7,
                "timeout": 30
            },
            "gpt-4": {
                "provider": "openai",
                "max_tokens": 8192,
                "temperature": 0.7,
                "timeout": 60
            },
            "claude-3-sonnet": {
                "provider": "anthropic",
                "max_tokens": 4096,
                "temperature": 0.7,
                "timeout": 45
            }
        }
        return configs.get(model_name, configs[self.DEFAULT_LLM_MODEL])


# Global settings instance
settings = Settings() 