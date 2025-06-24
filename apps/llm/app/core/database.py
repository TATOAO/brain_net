"""
Database connection manager for Brain_Net LLM Service
Handles connections to PostgreSQL, Elasticsearch, Neo4j, Redis, and MinIO
"""

import asyncio
from typing import Optional, Set, Dict, Any
import asyncpg
from elasticsearch import AsyncElasticsearch
from neo4j import AsyncGraphDatabase
import redis.asyncio as redis
from minio import Minio
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manages database connections for the LLM service."""
    
    def __init__(self):
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.elasticsearch: Optional[AsyncElasticsearch] = None
        self.neo4j_driver: Optional[Any] = None
        self.redis_client: Optional[redis.Redis] = None
        self.minio_client: Optional[Minio] = None
        self._failed_services: Set[str] = set()
    
    async def initialize(self) -> None:
        """Initialize all database connections with graceful failure handling."""
        logger.info("Initializing database connections for LLM service...")
        
        await asyncio.gather(
            self._init_postgres(),
            self._init_elasticsearch(),
            self._init_neo4j(),
            self._init_redis(),
            self._init_minio(),
            return_exceptions=True
        )
        
        available_services = self._get_available_services()
        logger.info(f"Database initialization complete. Available services: {available_services}")
        if self._failed_services:
            logger.warning(f"Failed to initialize services: {self._failed_services}")
    
    async def _init_postgres(self) -> None:
        """Initialize PostgreSQL connection pool."""
        try:
            self.postgres_pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("PostgreSQL connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {str(e)}")
            self._failed_services.add("postgres")
            raise
    
    async def _init_elasticsearch(self) -> None:
        """Initialize Elasticsearch connection."""
        try:
            self.elasticsearch = AsyncElasticsearch([settings.ELASTICSEARCH_URL])
            # Test connection
            await self.elasticsearch.ping()
            logger.info("Elasticsearch connection established successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Elasticsearch: {str(e)}")
            self._failed_services.add("elasticsearch")
            if self.elasticsearch:
                await self.elasticsearch.close()
                self.elasticsearch = None
    
    async def _init_neo4j(self) -> None:
        """Initialize Neo4j connection."""
        try:
            self.neo4j_driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            # Test connection
            await self.neo4j_driver.verify_connectivity()
            logger.info("Neo4j connection established successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Neo4j: {str(e)}")
            self._failed_services.add("neo4j")
            if self.neo4j_driver:
                await self.neo4j_driver.close()
                self.neo4j_driver = None
    
    async def _init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {str(e)}")
            self._failed_services.add("redis")
            if self.redis_client:
                await self.redis_client.close()
                self.redis_client = None
            raise
    
    async def _init_minio(self) -> None:
        """Initialize MinIO connection."""
        try:
            self.minio_client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=False
            )
            # Test connection by listing buckets
            list(self.minio_client.list_buckets())
            logger.info("MinIO connection established successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize MinIO: {str(e)}")
            self._failed_services.add("minio")
            self.minio_client = None
    
    def _get_available_services(self) -> list:
        """Get list of successfully initialized services."""
        all_services = ["postgres", "elasticsearch", "neo4j", "redis", "minio"]
        return [service for service in all_services if service not in self._failed_services]
    
    def get_failed_services(self) -> Set[str]:
        """Get set of failed services."""
        return self._failed_services.copy()
    
    @asynccontextmanager
    async def get_postgres_connection(self):
        """Get PostgreSQL connection from pool."""
        if not self.postgres_pool:
            raise ConnectionError("PostgreSQL pool not initialized")
        
        async with self.postgres_pool.acquire() as connection:
            yield connection
    
    @asynccontextmanager
    async def get_neo4j_session(self):
        """Get Neo4j session."""
        if not self.neo4j_driver:
            raise ConnectionError("Neo4j driver not initialized")
        
        async with self.neo4j_driver.session() as session:
            yield session
    
    async def close_all(self) -> None:
        """Close all database connections."""
        logger.info("Closing all database connections...")
        
        tasks = []
        
        if self.postgres_pool:
            tasks.append(self.postgres_pool.close())
        
        if self.elasticsearch:
            tasks.append(self.elasticsearch.close())
        
        if self.neo4j_driver:
            tasks.append(self.neo4j_driver.close())
        
        if self.redis_client:
            tasks.append(self.redis_client.close())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("All database connections closed")
    
    # Vector Store specific methods
    async def get_vector_store_client(self):
        """Get vector store client based on configuration."""
        if settings.VECTOR_STORE_TYPE == "elasticsearch":
            if not self.elasticsearch:
                raise ConnectionError("Elasticsearch not available for vector operations")
            return self.elasticsearch
        # Add other vector store types as needed
        else:
            raise NotImplementedError(f"Vector store type {settings.VECTOR_STORE_TYPE} not implemented")
    
    # Cache operations for model and embedding caching
    async def cache_set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """Set value in cache with TTL."""
        if not self.redis_client:
            logger.warning("Redis not available for caching")
            return False
        
        try:
            return await self.redis_client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Cache set failed: {str(e)}")
            return False
    
    async def cache_get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        if not self.redis_client:
            return None
        
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Cache get failed: {str(e)}")
            return None 