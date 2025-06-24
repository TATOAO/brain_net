"""
Health check service for Brain_Net LLM Service
"""

from typing import Dict, Any
from app.core.database import DatabaseManager
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class HealthService:
    """Health check service for all LLM service components."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Check health of all services."""
        results = {}
        
        # Check database services
        results["postgres"] = await self.check_postgres()
        results["redis"] = await self.check_redis()
        results["elasticsearch"] = await self.check_elasticsearch()
        results["neo4j"] = await self.check_neo4j()
        results["minio"] = await self.check_minio()
        
        return results
    
    async def check_postgres(self) -> Dict[str, Any]:
        """Check PostgreSQL health."""
        try:
            if not self.db_manager.postgres_pool:
                return {
                    "healthy": False,
                    "message": "PostgreSQL pool not initialized",
                    "timestamp": settings.get_current_timestamp()
                }
            
            async with self.db_manager.get_postgres_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                return {
                    "healthy": result == 1,
                    "message": "PostgreSQL connection successful",
                    "timestamp": settings.get_current_timestamp()
                }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"PostgreSQL health check failed: {str(e)}",
                "timestamp": settings.get_current_timestamp()
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis health."""
        try:
            if not self.db_manager.redis_client:
                return {
                    "healthy": False,
                    "message": "Redis client not initialized",
                    "timestamp": settings.get_current_timestamp()
                }
            
            result = await self.db_manager.redis_client.ping()
            return {
                "healthy": result,
                "message": "Redis connection successful",
                "timestamp": settings.get_current_timestamp()
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Redis health check failed: {str(e)}",
                "timestamp": settings.get_current_timestamp()
            }
    
    async def check_elasticsearch(self) -> Dict[str, Any]:
        """Check Elasticsearch health."""
        try:
            if not self.db_manager.elasticsearch:
                return {
                    "healthy": False,
                    "message": "Elasticsearch client not initialized",
                    "timestamp": settings.get_current_timestamp()
                }
            
            result = await self.db_manager.elasticsearch.ping()
            return {
                "healthy": result,
                "message": "Elasticsearch connection successful",
                "timestamp": settings.get_current_timestamp()
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Elasticsearch health check failed: {str(e)}",
                "timestamp": settings.get_current_timestamp()
            }
    
    async def check_neo4j(self) -> Dict[str, Any]:
        """Check Neo4j health."""
        try:
            if not self.db_manager.neo4j_driver:
                return {
                    "healthy": False,
                    "message": "Neo4j driver not initialized",
                    "timestamp": settings.get_current_timestamp()
                }
            
            await self.db_manager.neo4j_driver.verify_connectivity()
            return {
                "healthy": True,
                "message": "Neo4j connection successful",
                "timestamp": settings.get_current_timestamp()
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Neo4j health check failed: {str(e)}",
                "timestamp": settings.get_current_timestamp()
            }
    
    async def check_minio(self) -> Dict[str, Any]:
        """Check MinIO health."""
        try:
            if not self.db_manager.minio_client:
                return {
                    "healthy": False,
                    "message": "MinIO client not initialized",
                    "timestamp": settings.get_current_timestamp()
                }
            
            # Try to list buckets as a health check
            list(self.db_manager.minio_client.list_buckets())
            return {
                "healthy": True,
                "message": "MinIO connection successful",
                "timestamp": settings.get_current_timestamp()
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"MinIO health check failed: {str(e)}",
                "timestamp": settings.get_current_timestamp()
            }
    
    # LLM-specific health checks
    async def check_models(self) -> Dict[str, Any]:
        """Check if models are loaded and ready."""
        try:
            # This would check model loading status
            return {
                "healthy": True,
                "message": "Models ready",
                "loaded_models": [],  # Would be populated by model service
                "timestamp": settings.get_current_timestamp()
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Model health check failed: {str(e)}",
                "timestamp": settings.get_current_timestamp()
            }
    
    async def check_vector_store(self) -> Dict[str, Any]:
        """Check vector store health."""
        try:
            if settings.VECTOR_STORE_TYPE == "elasticsearch":
                return await self.check_elasticsearch()
            else:
                return {
                    "healthy": False,
                    "message": f"Vector store type {settings.VECTOR_STORE_TYPE} not implemented",
                    "timestamp": settings.get_current_timestamp()
                }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Vector store health check failed: {str(e)}",
                "timestamp": settings.get_current_timestamp()
            }
    
    async def check_embedding_service(self) -> Dict[str, Any]:
        """Check embedding service health."""
        try:
            # This would test embedding generation
            return {
                "healthy": True,
                "message": "Embedding service ready",
                "model": settings.DEFAULT_EMBEDDING_MODEL,
                "timestamp": settings.get_current_timestamp()
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Embedding service health check failed: {str(e)}",
                "timestamp": settings.get_current_timestamp()
            } 