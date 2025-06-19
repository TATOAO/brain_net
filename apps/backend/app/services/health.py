"""
Health check service for Brain_Net Backend
Provides comprehensive health checks for all database services.
"""

import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import text

from app.core.database import DatabaseManager
from app.core.config import settings
from app.core.logging import LoggerMixin


class HealthService(LoggerMixin):
    """Service for performing health checks on all system components."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._last_check_time = None
        self._cached_health_status = None
        self._cache_duration = timedelta(seconds=30)  # Cache for 30 seconds
    
    async def check_all_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Perform health checks on all services.
        Returns cached results if checked recently.
        """
        now = datetime.utcnow()
        
        # Return cached results if available and not expired
        if (self._last_check_time and self._cached_health_status and 
            now - self._last_check_time < self._cache_duration):
            return self._cached_health_status
        
        self.logger.info("Performing comprehensive health check...")
        start_time = time.time()
        
        # Run all health checks concurrently
        health_checks = await asyncio.gather(
            self.check_postgres(),
            self.check_elasticsearch(),
            self.check_neo4j(),
            self.check_minio(),
            self.check_redis(),
            return_exceptions=True
        )
        
        # Process results
        service_names = ["postgres", "elasticsearch", "neo4j", "minio", "redis"]
        health_status = {}
        
        for i, (service_name, result) in enumerate(zip(service_names, health_checks)):
            if isinstance(result, Exception):
                health_status[service_name] = {
                    "healthy": False,
                    "message": f"Health check failed: {str(result)}",
                    "error": str(result),
                    "timestamp": now.isoformat() + "Z"
                }
            else:
                health_status[service_name] = result
        
        # Calculate total check time
        total_time = time.time() - start_time
        
        # Add metadata
        for service_status in health_status.values():
            service_status["check_duration_ms"] = round(total_time * 1000, 2)
        
        # Cache results
        self._last_check_time = now
        self._cached_health_status = health_status
        
        # Log summary
        healthy_count = sum(1 for status in health_status.values() if status["healthy"])
        total_count = len(health_status)
        self.logger.info(f"Health check completed: {healthy_count}/{total_count} services healthy")
        
        return health_status
    
    async def check_postgres(self) -> Dict[str, Any]:
        """Perform detailed PostgreSQL health check."""
        start_time = time.time()
        
        try:
            # Basic connectivity check
            async with self.db_manager.postgres_engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.fetchone()
            
            # Get database info
            async with self.db_manager.postgres_engine.begin() as conn:
                # Get version
                version_result = await conn.execute(text("SELECT version()"))
                version = version_result.fetchone()[0]
                
                # Get database size
                size_result = await conn.execute(text(
                    "SELECT pg_size_pretty(pg_database_size(current_database()))"
                ))
                db_size = size_result.fetchone()[0]
                
                # Get connection count
                conn_result = await conn.execute(text(
                    "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
                ))
                active_connections = conn_result.fetchone()[0]
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            return {
                "healthy": True,
                "message": "PostgreSQL is healthy",
                "details": {
                    "version": version.split()[1] if version else "Unknown",
                    "database_size": db_size,
                    "active_connections": active_connections,
                    "response_time_ms": response_time
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            response_time = round((time.time() - start_time) * 1000, 2)
            self.logger.error(f"PostgreSQL health check failed: {str(e)}")
            
            return {
                "healthy": False,
                "message": f"PostgreSQL health check failed: {str(e)}",
                "error": str(e),
                "details": {
                    "response_time_ms": response_time
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def check_elasticsearch(self) -> Dict[str, Any]:
        """Perform detailed Elasticsearch health check."""
        start_time = time.time()
        
        try:
            # Basic connectivity check
            await self.db_manager.elasticsearch.ping()
            
            # Get cluster health
            cluster_health = await self.db_manager.elasticsearch.cluster.health()
            
            # Get cluster info
            cluster_info = await self.db_manager.elasticsearch.info()
            
            # Get indices info
            indices_stats = await self.db_manager.elasticsearch.cat.indices(
                format="json", bytes="b"
            )
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            return {
                "healthy": cluster_health["status"] in ["green", "yellow"],
                "message": f"Elasticsearch cluster status: {cluster_health['status']}",
                "details": {
                    "cluster_name": cluster_health["cluster_name"],
                    "status": cluster_health["status"],
                    "number_of_nodes": cluster_health["number_of_nodes"],
                    "active_primary_shards": cluster_health["active_primary_shards"],
                    "active_shards": cluster_health["active_shards"],
                    "version": cluster_info["version"]["number"],
                    "indices_count": len(indices_stats) if indices_stats else 0,
                    "response_time_ms": response_time
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            response_time = round((time.time() - start_time) * 1000, 2)
            self.logger.error(f"Elasticsearch health check failed: {str(e)}")
            
            return {
                "healthy": False,
                "message": f"Elasticsearch health check failed: {str(e)}",
                "error": str(e),
                "details": {
                    "response_time_ms": response_time
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def check_neo4j(self) -> Dict[str, Any]:
        """Perform detailed Neo4j health check."""
        start_time = time.time()
        
        try:
            # Basic connectivity check
            await self.db_manager.neo4j.verify_connectivity()
            
            # Get database info
            async with self.db_manager.get_neo4j_session() as session:
                # Get version
                version_result = await session.run("CALL dbms.components() YIELD versions")
                version_record = await version_result.single()
                version = version_record["versions"][0] if version_record else "Unknown"
                
                # Get node count
                node_result = await session.run("MATCH (n) RETURN count(n) as count")
                node_count = (await node_result.single())["count"]
                
                # Get relationship count
                rel_result = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = (await rel_result.single())["count"]
                
                # Get database name
                db_result = await session.run("CALL db.info()")
                db_info = await db_result.single()
                db_name = db_info["name"] if db_info else settings.NEO4J_DATABASE
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            return {
                "healthy": True,
                "message": "Neo4j is healthy",
                "details": {
                    "version": version,
                    "database": db_name,
                    "node_count": node_count,
                    "relationship_count": rel_count,
                    "response_time_ms": response_time
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            response_time = round((time.time() - start_time) * 1000, 2)
            self.logger.error(f"Neo4j health check failed: {str(e)}")
            
            return {
                "healthy": False,
                "message": f"Neo4j health check failed: {str(e)}",
                "error": str(e),
                "details": {
                    "response_time_ms": response_time
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def check_minio(self) -> Dict[str, Any]:
        """Perform detailed MinIO health check."""
        start_time = time.time()
        
        try:
            # Check if bucket exists
            bucket_exists = self.db_manager.minio.bucket_exists(settings.MINIO_BUCKET_NAME)
            
            # Get bucket stats
            objects = list(self.db_manager.minio.list_objects(settings.MINIO_BUCKET_NAME))
            object_count = len(objects)
            
            # Calculate total size
            total_size = sum(obj.size for obj in objects if obj.size)
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            return {
                "healthy": bucket_exists,
                "message": f"MinIO bucket '{settings.MINIO_BUCKET_NAME}' is accessible",
                "details": {
                    "bucket_name": settings.MINIO_BUCKET_NAME,
                    "bucket_exists": bucket_exists,
                    "object_count": object_count,
                    "total_size_bytes": total_size,
                    "response_time_ms": response_time
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            response_time = round((time.time() - start_time) * 1000, 2)
            self.logger.error(f"MinIO health check failed: {str(e)}")
            
            return {
                "healthy": False,
                "message": f"MinIO health check failed: {str(e)}",
                "error": str(e),
                "details": {
                    "response_time_ms": response_time
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Perform detailed Redis health check."""
        start_time = time.time()
        
        try:
            # Basic connectivity check
            await self.db_manager.redis.ping()
            
            # Get Redis info
            info = await self.db_manager.redis.info()
            
            # Get memory usage
            memory_info = await self.db_manager.redis.info("memory")
            
            # Get keyspace info
            keyspace_info = await self.db_manager.redis.info("keyspace")
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            return {
                "healthy": True,
                "message": "Redis is healthy",
                "details": {
                    "version": info.get("redis_version", "Unknown"),
                    "mode": info.get("redis_mode", "Unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": memory_info.get("used_memory", 0),
                    "used_memory_human": memory_info.get("used_memory_human", "0B"),
                    "keyspace": keyspace_info,
                    "response_time_ms": response_time
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            response_time = round((time.time() - start_time) * 1000, 2)
            self.logger.error(f"Redis health check failed: {str(e)}")
            
            return {
                "healthy": False,
                "message": f"Redis health check failed: {str(e)}",
                "error": str(e),
                "details": {
                    "response_time_ms": response_time
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    def clear_cache(self) -> None:
        """Clear cached health check results."""
        self._last_check_time = None
        self._cached_health_status = None
        self.logger.info("Health check cache cleared") 