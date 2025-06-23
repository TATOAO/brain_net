"""
Database connection manager for Brain_Net Backend
Manages connections to PostgreSQL, Elasticsearch, Neo4j, MinIO, and Redis.
"""

import asyncio
from typing import Optional, Dict, Any
import logging
from contextlib import asynccontextmanager

# Database clients
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from elasticsearch import AsyncElasticsearch
from neo4j import AsyncGraphDatabase
from minio import Minio
import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import LoggerMixin


class DatabaseManager(LoggerMixin):
    """Manages all database connections for the application."""
    
    def __init__(self):
        self._postgres_engine = None
        self._postgres_session_factory = None
        self._elasticsearch_client = None
        self._neo4j_driver = None
        self._minio_client = None
        self._redis_client = None
        self._initialized = False
        self._failed_services = set()  # Track which optional services failed to initialize
    
    async def initialize(self) -> None:
        """Initialize all database connections."""
        if self._initialized:
            self.logger.warning("Database manager already initialized")
            return
        
        self.logger.info("Initializing database connections...")
        
        # Initialize required services first
        required_failures = []
        
        # Initialize PostgreSQL (always required)
        try:
            await self._init_postgres()
            self.logger.info("PostgreSQL initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize required service PostgreSQL: {str(e)}")
            required_failures.append(("postgres", str(e)))
        
        # If required services failed and graceful degradation is disabled, fail fast
        if required_failures and not settings.ENABLE_GRACEFUL_DEGRADATION:
            await self.close_all()
            raise RuntimeError(f"Required services failed to initialize: {[f[0] for f in required_failures]}")
        
        # Initialize optional services
        optional_init_tasks = [
            ("elasticsearch", self._init_elasticsearch()),
            ("neo4j", self._init_neo4j()),
            ("minio", self._init_minio()),
            ("redis", self._init_redis())
        ]
        
        for service_name, init_task in optional_init_tasks:
            try:
                await init_task
                self.logger.info(f"{service_name.capitalize()} initialized successfully")
            except Exception as e:
                if service_name in settings.REQUIRED_SERVICES:
                    self.logger.error(f"Failed to initialize required service {service_name}: {str(e)}")
                    required_failures.append((service_name, str(e)))
                else:
                    self.logger.warning(f"Failed to initialize optional service {service_name}: {str(e)}")
                    self._failed_services.add(service_name)
        
        # Check if we have any required service failures
        if required_failures:
            await self.close_all()
            raise RuntimeError(f"Required services failed to initialize: {[f[0] for f in required_failures]}")
        
        self._initialized = True
        
        # Log initialization summary
        if self._failed_services:
            self.logger.warning(f"Application started with degraded functionality. Failed optional services: {list(self._failed_services)}")
        else:
            self.logger.info("All database connections initialized successfully")
        
        self.logger.info(f"Database manager initialized. Available services: {self._get_available_services()}")
    
    async def _init_postgres(self) -> None:
        """Initialize PostgreSQL connection."""
        try:
            self.logger.info("Initializing PostgreSQL connection...")
            
            # Create async engine
            self._postgres_engine = create_async_engine(
                settings.get_database_url(async_driver=True),
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                echo=settings.DEBUG_SQL,
                future=True
            )
            
            # Create session factory
            self._postgres_session_factory = async_sessionmaker(
                bind=self._postgres_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self._postgres_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            self.logger.info("PostgreSQL connection established")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PostgreSQL: {str(e)}")
            raise
    
    async def _init_elasticsearch(self) -> None:
        """Initialize Elasticsearch connection."""
        try:
            self.logger.info("Initializing Elasticsearch connection...")
            
            self._elasticsearch_client = AsyncElasticsearch(
                hosts=[settings.ELASTICSEARCH_URL],
                timeout=settings.ELASTICSEARCH_TIMEOUT,
                retry_on_timeout=True,
                max_retries=3
            )
            
            # Test connection
            await self._elasticsearch_client.ping()
            
            self.logger.info("Elasticsearch connection established")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Elasticsearch: {str(e)}")
            raise
    
    async def _init_neo4j(self) -> None:
        """Initialize Neo4j connection."""
        try:
            self.logger.info("Initializing Neo4j connection...")
            
            self._neo4j_driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            
            # Test connection
            await self._neo4j_driver.verify_connectivity()
            
            self.logger.info("Neo4j connection established")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Neo4j: {str(e)}")
            raise
    
    async def _init_minio(self) -> None:
        """Initialize MinIO connection."""
        try:
            self.logger.info("Initializing MinIO connection...")
            
            self._minio_client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            
            # Test connection and create bucket if it doesn't exist
            bucket_exists = self._minio_client.bucket_exists(settings.MINIO_BUCKET_NAME)
            if not bucket_exists:
                self._minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
                self.logger.info(f"Created MinIO bucket: {settings.MINIO_BUCKET_NAME}")
            
            self.logger.info("MinIO connection established")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MinIO: {str(e)}")
            raise
    
    async def _init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            self.logger.info("Initializing Redis connection...")
            
            # Parse Redis URL
            redis_url = settings.REDIS_URL
            if settings.REDIS_PASSWORD:
                # Insert password into URL if provided
                redis_url = redis_url.replace("redis://", f"redis://:{settings.REDIS_PASSWORD}@")
            
            self._redis_client = redis.from_url(
                redis_url,
                db=settings.REDIS_DB,
                socket_timeout=settings.REDIS_TIMEOUT,
                socket_connect_timeout=settings.REDIS_TIMEOUT,
                retry_on_timeout=True
            )
            
            # Test connection
            await self._redis_client.ping()
            
            self.logger.info("Redis connection established")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis: {str(e)}")
            raise
    
    async def close_all(self) -> None:
        """Close all database connections."""
        self.logger.info("Closing all database connections...")
        
        # Close Redis
        if self._redis_client:
            try:
                await self._redis_client.close()
                self.logger.info("Redis connection closed")
            except Exception as e:
                self.logger.error(f"Error closing Redis connection: {str(e)}")
        
        # Close Neo4j
        if self._neo4j_driver:
            try:
                await self._neo4j_driver.close()
                self.logger.info("Neo4j connection closed")
            except Exception as e:
                self.logger.error(f"Error closing Neo4j connection: {str(e)}")
        
        # Close Elasticsearch
        if self._elasticsearch_client:
            try:
                await self._elasticsearch_client.close()
                self.logger.info("Elasticsearch connection closed")
            except Exception as e:
                self.logger.error(f"Error closing Elasticsearch connection: {str(e)}")
        
        # Close PostgreSQL
        if self._postgres_engine:
            try:
                await self._postgres_engine.dispose()
                self.logger.info("PostgreSQL connection closed")
            except Exception as e:
                self.logger.error(f"Error closing PostgreSQL connection: {str(e)}")
        
        self._initialized = False
        self._failed_services.clear()
        self.logger.info("All database connections closed")
    
    def _get_available_services(self) -> list:
        """Get list of successfully initialized services."""
        available = []
        if self._postgres_engine:
            available.append("postgres")
        if self._elasticsearch_client:
            available.append("elasticsearch")
        if self._neo4j_driver:
            available.append("neo4j")
        if self._minio_client:
            available.append("minio")
        if self._redis_client:
            available.append("redis")
        return available
    
    def is_service_available(self, service_name: str) -> bool:
        """Check if a specific service is available."""
        return service_name not in self._failed_services and getattr(self, f"_{service_name}_client", None) is not None or (service_name == "postgres" and self._postgres_engine is not None)
    
    def get_failed_services(self) -> set:
        """Get set of services that failed to initialize."""
        return self._failed_services.copy()
    
    # Property accessors for database clients
    @property
    def postgres_engine(self):
        """Get PostgreSQL engine."""
        if not self._initialized or not self._postgres_engine:
            raise RuntimeError("PostgreSQL not initialized")
        return self._postgres_engine
    
    @property
    def postgres_session_factory(self):
        """Get PostgreSQL session factory."""
        if not self._initialized or not self._postgres_session_factory:
            raise RuntimeError("PostgreSQL not initialized")
        return self._postgres_session_factory
    
    @property
    def elasticsearch(self):
        """Get Elasticsearch client."""
        if not self._initialized:
            raise RuntimeError("Database manager not initialized")
        if not self._elasticsearch_client:
            if "elasticsearch" in self._failed_services:
                raise RuntimeError("Elasticsearch is not available (failed to initialize)")
            else:
                raise RuntimeError("Elasticsearch not initialized")
        return self._elasticsearch_client
    
    @property
    def neo4j(self):
        """Get Neo4j driver."""
        if not self._initialized:
            raise RuntimeError("Database manager not initialized")
        if not self._neo4j_driver:
            if "neo4j" in self._failed_services:
                raise RuntimeError("Neo4j is not available (failed to initialize)")
            else:
                raise RuntimeError("Neo4j not initialized")
        return self._neo4j_driver
    
    @property
    def minio(self):
        """Get MinIO client."""
        if not self._initialized:
            raise RuntimeError("Database manager not initialized")
        if not self._minio_client:
            if "minio" in self._failed_services:
                raise RuntimeError("MinIO is not available (failed to initialize)")
            else:
                raise RuntimeError("MinIO not initialized")
        return self._minio_client
    
    @property
    def redis(self):
        """Get Redis client."""
        if not self._initialized:
            raise RuntimeError("Database manager not initialized")
        if not self._redis_client:
            if "redis" in self._failed_services:
                raise RuntimeError("Redis is not available (failed to initialize)")
            else:
                raise RuntimeError("Redis not initialized")
        return self._redis_client
    
    # Safe accessor methods for optional services
    def get_elasticsearch_safe(self):
        """Get Elasticsearch client safely, returns None if not available."""
        if self._initialized and self._elasticsearch_client and "elasticsearch" not in self._failed_services:
            return self._elasticsearch_client
        return None
    
    def get_neo4j_safe(self):
        """Get Neo4j driver safely, returns None if not available."""
        if self._initialized and self._neo4j_driver and "neo4j" not in self._failed_services:
            return self._neo4j_driver
        return None
    
    def get_minio_safe(self):
        """Get MinIO client safely, returns None if not available."""
        if self._initialized and self._minio_client and "minio" not in self._failed_services:
            return self._minio_client
        return None
    
    def get_redis_safe(self):
        """Get Redis client safely, returns None if not available."""
        if self._initialized and self._redis_client and "redis" not in self._failed_services:
            return self._redis_client
        return None
    
    @asynccontextmanager
    async def get_postgres_session(self):
        """Get PostgreSQL session context manager."""
        async with self.postgres_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    @asynccontextmanager
    async def get_neo4j_session(self):
        """Get Neo4j session context manager."""
        async with self.neo4j.session(database=settings.NEO4J_DATABASE) as session:
            yield session
    
    @asynccontextmanager
    async def get_neo4j_session_safe(self):
        """Get Neo4j session context manager safely, yields None if not available."""
        neo4j_driver = self.get_neo4j_safe()
        if neo4j_driver:
            async with neo4j_driver.session(database=settings.NEO4J_DATABASE) as session:
                yield session
        else:
            yield None
    
    async def health_check(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all database connections."""
        health_status = {}
        
        # Check PostgreSQL
        try:
            async with self.postgres_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            health_status["postgres"] = {"healthy": True, "message": "Connected"}
        except Exception as e:
            health_status["postgres"] = {"healthy": False, "message": str(e)}
        
        # Check Elasticsearch
        try:
            await self.elasticsearch.ping()
            health_status["elasticsearch"] = {"healthy": True, "message": "Connected"}
        except Exception as e:
            health_status["elasticsearch"] = {"healthy": False, "message": str(e)}
        
        # Check Neo4j
        try:
            await self.neo4j.verify_connectivity()
            health_status["neo4j"] = {"healthy": True, "message": "Connected"}
        except Exception as e:
            health_status["neo4j"] = {"healthy": False, "message": str(e)}
        
        # Check MinIO
        try:
            self.minio.bucket_exists(settings.MINIO_BUCKET_NAME)
            health_status["minio"] = {"healthy": True, "message": "Connected"}
        except Exception as e:
            health_status["minio"] = {"healthy": False, "message": str(e)}
        
        # Check Redis
        try:
            await self.redis.ping()
            health_status["redis"] = {"healthy": True, "message": "Connected"}
        except Exception as e:
            health_status["redis"] = {"healthy": False, "message": str(e)}
        
        return health_status 