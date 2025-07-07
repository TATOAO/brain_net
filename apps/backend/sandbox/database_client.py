"""
Database HTTP client for sandbox containers.
Provides secure access to databases via the main application's API.
"""

import aiohttp
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from app.core.logging import LoggerMixin


class DatabaseError(Exception):
    """Custom exception for database operation errors."""
    pass


class DatabaseClient(LoggerMixin):
    """HTTP client for database operations in sandbox environment."""
    
    def __init__(self, base_url: str, auth_token: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.timeout = timeout
        self.session = None
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize aiohttp session with authentication headers."""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    # PostgreSQL Operations
    async def execute_postgres_query(self, query: str, params: Dict[str, Any] = None,
                                   execution_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute PostgreSQL query via main app API."""
        
        request_data = {
            "query": query,
            "params": params or {},
            "execution_context": execution_context
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/db/postgres/query",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.debug(f"PostgreSQL query executed successfully: {query[:100]}...")
                    return result
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('detail', f'HTTP {response.status}')
                    self.logger.error(f"PostgreSQL query failed: {error_msg}")
                    raise DatabaseError(f"PostgreSQL query failed: {error_msg}")
                    
        except aiohttp.ClientError as e:
            self.logger.error(f"Network error during PostgreSQL query: {e}")
            raise DatabaseError(f"Network error: {str(e)}")
    
    async def execute_postgres_batch(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple PostgreSQL queries in batch."""
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/db/postgres/batch",
                json=queries
            ) as response:
                if response.status == 200:
                    results = await response.json()
                    self.logger.debug(f"PostgreSQL batch executed: {len(queries)} queries")
                    return results
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('detail', f'HTTP {response.status}')
                    raise DatabaseError(f"PostgreSQL batch failed: {error_msg}")
                    
        except aiohttp.ClientError as e:
            raise DatabaseError(f"Network error: {str(e)}")
    
    # Elasticsearch Operations
    async def elasticsearch_search(self, index: str, query: Dict[str, Any],
                                 size: int = 10, from_: int = 0,
                                 execution_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute Elasticsearch search via main app API."""
        
        request_data = {
            "index": index,
            "query": query,
            "size": size,
            "from": from_,
            "execution_context": execution_context
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/db/elasticsearch/search",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.debug(f"Elasticsearch search executed on index: {index}")
                    return result
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('detail', f'HTTP {response.status}')
                    raise DatabaseError(f"Elasticsearch search failed: {error_msg}")
                    
        except aiohttp.ClientError as e:
            raise DatabaseError(f"Network error: {str(e)}")
    
    async def elasticsearch_index(self, index: str, document: Dict[str, Any],
                                doc_id: Optional[str] = None) -> Dict[str, Any]:
        """Index document in Elasticsearch via main app API."""
        
        request_data = {
            "index": index,
            "document": document,
            "id": doc_id
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/db/elasticsearch/index",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.debug(f"Document indexed in Elasticsearch: {index}")
                    return result
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('detail', f'HTTP {response.status}')
                    raise DatabaseError(f"Elasticsearch indexing failed: {error_msg}")
                    
        except aiohttp.ClientError as e:
            raise DatabaseError(f"Network error: {str(e)}")
    
    # Neo4j Operations
    async def execute_neo4j_query(self, query: str, params: Dict[str, Any] = None,
                                database: Optional[str] = None,
                                execution_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute Neo4j query via main app API."""
        
        request_data = {
            "query": query,
            "params": params or {},
            "database": database,
            "execution_context": execution_context
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/db/neo4j/query",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.debug(f"Neo4j query executed successfully")
                    return result
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('detail', f'HTTP {response.status}')
                    raise DatabaseError(f"Neo4j query failed: {error_msg}")
                    
        except aiohttp.ClientError as e:
            raise DatabaseError(f"Network error: {str(e)}")
    
    # Redis Operations
    async def execute_redis_command(self, command: str, args: List[Any] = None,
                                  execution_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute Redis command via main app API."""
        
        request_data = {
            "command": command,
            "args": args or [],
            "execution_context": execution_context
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/db/redis/command",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.debug(f"Redis command executed: {command}")
                    return result
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('detail', f'HTTP {response.status}')
                    raise DatabaseError(f"Redis command failed: {error_msg}")
                    
        except aiohttp.ClientError as e:
            raise DatabaseError(f"Network error: {str(e)}")
    
    # Convenience methods for common operations
    async def save_processor_result(self, processor_id: int, step_index: int,
                                  input_data: Any, output_data: Any) -> Dict[str, Any]:
        """Save processor execution result to database."""
        
        request_data = {
            "processor_id": processor_id,
            "step_index": step_index,
            "input_data": self._serialize_data(input_data),
            "output_data": self._serialize_data(output_data)
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/db/postgres/save-processor-result",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.debug(f"Processor result saved: processor {processor_id}, step {step_index}")
                    return result
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('detail', f'HTTP {response.status}')
                    raise DatabaseError(f"Failed to save processor result: {error_msg}")
                    
        except aiohttp.ClientError as e:
            raise DatabaseError(f"Network error: {str(e)}")
    
    async def save_vectors(self, collection_name: str, vectors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Save vectors to Elasticsearch."""
        
        request_data = {
            "collection_name": collection_name,
            "vectors": vectors
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/db/elasticsearch/save-vectors",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.debug(f"Vectors saved: {len(vectors)} vectors to {collection_name}")
                    return result
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('detail', f'HTTP {response.status}')
                    raise DatabaseError(f"Failed to save vectors: {error_msg}")
                    
        except aiohttp.ClientError as e:
            raise DatabaseError(f"Network error: {str(e)}")
    
    async def save_relationships(self, relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Save relationships to Neo4j."""
        
        request_data = {
            "relationships": relationships
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/db/neo4j/save-relationships",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.debug(f"Relationships saved: {len(relationships)} relationships")
                    return result
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('detail', f'HTTP {response.status}')
                    raise DatabaseError(f"Failed to save relationships: {error_msg}")
                    
        except aiohttp.ClientError as e:
            raise DatabaseError(f"Network error: {str(e)}")
    
    async def search_knowledge_base(self, query: str, index: str = "knowledge_base",
                                  size: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge base via Elasticsearch."""
        
        search_query = {
            "match": {
                "content": query
            }
        }
        
        result = await self.elasticsearch_search(
            index=index,
            query=search_query,
            size=size
        )
        
        # Extract hits from Elasticsearch response
        hits = result.get('data', {}).get('hits', {}).get('hits', [])
        return [hit['_source'] for hit in hits]
    
    async def store_cache_data(self, key: str, value: Any, ttl: int = 3600) -> Dict[str, Any]:
        """Store data in Redis cache."""
        
        serialized_value = json.dumps(value, default=str)
        
        # Set value with TTL
        await self.execute_redis_command("SET", [key, serialized_value])
        await self.execute_redis_command("EXPIRE", [key, ttl])
        
        return {"success": True, "key": key, "ttl": ttl}
    
    async def get_cache_data(self, key: str) -> Any:
        """Get data from Redis cache."""
        
        result = await self.execute_redis_command("GET", [key])
        
        if result['success'] and result['data']:
            try:
                return json.loads(result['data'])
            except json.JSONDecodeError:
                return result['data']  # Return as string if not JSON
        
        return None
    
    # Utility and monitoring methods
    async def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit logs for current execution."""
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/db/audit/logs?limit={limit}"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('logs', [])
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('detail', f'HTTP {response.status}')
                    raise DatabaseError(f"Failed to get audit logs: {error_msg}")
                    
        except aiohttp.ClientError as e:
            raise DatabaseError(f"Network error: {str(e)}")
    
    async def validate_query(self, database_type: str, operation: str, query: str) -> Dict[str, Any]:
        """Validate query without executing it."""
        
        request_data = {
            "database_type": database_type,
            "operation": operation,
            "query": query
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/db/debug/validate-query",
                json=request_data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('detail', f'HTTP {response.status}')
                    raise DatabaseError(f"Query validation failed: {error_msg}")
                    
        except aiohttp.ClientError as e:
            raise DatabaseError(f"Network error: {str(e)}")
    
    async def get_permissions(self) -> Dict[str, Any]:
        """Get current user's database permissions."""
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/db/permissions"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    error_msg = error_data.get('detail', f'HTTP {response.status}')
                    raise DatabaseError(f"Failed to get permissions: {error_msg}")
                    
        except aiohttp.ClientError as e:
            raise DatabaseError(f"Network error: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database API health."""
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/db/health"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "unhealthy", "code": response.status}
                    
        except aiohttp.ClientError as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def _serialize_data(self, data: Any) -> Any:
        """Serialize data for JSON transmission."""
        if data is None:
            return None
        
        # Handle common types that need serialization
        if isinstance(data, (datetime,)):
            return data.isoformat()
        elif hasattr(data, '__dict__'):
            # For objects with __dict__, convert to dict
            return data.__dict__
        elif isinstance(data, (list, tuple)):
            return [self._serialize_data(item) for item in data]
        elif isinstance(data, dict):
            return {key: self._serialize_data(value) for key, value in data.items()}
        else:
            # For other types, try to convert to string
            try:
                json.dumps(data)  # Test if it's JSON serializable
                return data
            except (TypeError, ValueError):
                return str(data)


# Factory function for creating database clients
async def create_database_client(base_url: str, auth_token: str, timeout: int = 30) -> DatabaseClient:
    """Create and return a configured database client."""
    return DatabaseClient(base_url, auth_token, timeout)


# Context manager for automatic session management
class ManagedDatabaseClient:
    """Context manager for automatic database client session management."""
    
    def __init__(self, base_url: str, auth_token: str, timeout: int = 30):
        self.base_url = base_url
        self.auth_token = auth_token
        self.timeout = timeout
        self.client = None
    
    async def __aenter__(self) -> DatabaseClient:
        self.client = DatabaseClient(self.base_url, self.auth_token, self.timeout)
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.close() 