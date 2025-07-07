"""
Enhanced processor classes for sandbox environment with HTTP database access.
"""

import asyncio
import json
from typing import AsyncGenerator, Any, Dict, List, Optional
from datetime import datetime
from processor_pipeline import AsyncProcessor
from sandbox.database_client import DatabaseClient, DatabaseError


class SandboxAsyncProcessor(AsyncProcessor):
    """Enhanced AsyncProcessor for sandbox environment with secure database access."""
    
    def __init__(self, config: Dict[str, Any], db_client: DatabaseClient):
        super().__init__(config)
        self.db_client = db_client
        self.execution_context = config.get('execution_context', {})
        self.debug_mode = config.get('debug_mode', False)
        self.save_intermediate_results = config.get('save_intermediate_results', True)
        
        # Initialize processor metadata
        if not hasattr(self, 'meta'):
            self.meta = {
                'name': self.__class__.__name__,
                'version': '1.0.0',
                'input_type': 'Any',
                'output_type': 'Any'
            }
    
    async def process(self, data: AsyncGenerator[Any, None]) -> AsyncGenerator[Any, None]:
        """
        Override this method in subclasses to implement processor logic.
        This base implementation just passes data through.
        """
        async for item in data:
            yield item
    
    async def save_intermediate_result(self, step_name: str, data: Any, 
                                     metadata: Dict[str, Any] = None) -> bool:
        """Save intermediate processing result to database."""
        
        if not self.save_intermediate_results:
            return False
        
        try:
            result_data = {
                "step_name": step_name,
                "data": data,
                "metadata": metadata or {},
                "processor_name": self.meta.get('name'),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.db_client.save_processor_result(
                processor_id=self.meta.get('id', 0),
                step_index=self.execution_context.get('step_index', 0),
                input_data=None,
                output_data=result_data
            )
            
            if self.debug_mode:
                self.logger.info(f"Saved intermediate result for step: {step_name}")
            
            return True
            
        except DatabaseError as e:
            self.logger.warning(f"Failed to save intermediate result: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error saving intermediate result: {e}")
            return False
    
    async def search_knowledge_base(self, query: str, index: str = "knowledge_base",
                                  size: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge base via Elasticsearch."""
        
        try:
            results = await self.db_client.search_knowledge_base(
                query=query,
                index=index,
                size=size
            )
            
            if self.debug_mode:
                self.logger.info(f"Knowledge base search returned {len(results)} results for query: {query[:50]}...")
            
            return results
            
        except DatabaseError as e:
            self.logger.error(f"Knowledge base search failed: {e}")
            return []
    
    async def store_vectors(self, vectors: List[Dict[str, Any]], 
                          collection_name: str) -> bool:
        """Store vectors in Elasticsearch."""
        
        try:
            result = await self.db_client.save_vectors(
                collection_name=collection_name,
                vectors=vectors
            )
            
            if self.debug_mode:
                self.logger.info(f"Stored {len(vectors)} vectors in collection: {collection_name}")
            
            return result.get('success', False)
            
        except DatabaseError as e:
            self.logger.error(f"Failed to store vectors: {e}")
            return False
    
    async def store_relationships(self, relationships: List[Dict[str, Any]]) -> bool:
        """Store relationships in Neo4j."""
        
        try:
            result = await self.db_client.save_relationships(relationships)
            
            if self.debug_mode:
                self.logger.info(f"Stored {len(relationships)} relationships")
            
            return result.get('success', False)
            
        except DatabaseError as e:
            self.logger.error(f"Failed to store relationships: {e}")
            return False
    
    async def cache_data(self, key: str, data: Any, ttl: int = 3600) -> bool:
        """Cache data in Redis."""
        
        try:
            result = await self.db_client.store_cache_data(key, data, ttl)
            
            if self.debug_mode:
                self.logger.info(f"Cached data with key: {key} (TTL: {ttl}s)")
            
            return result.get('success', False)
            
        except DatabaseError as e:
            self.logger.error(f"Failed to cache data: {e}")
            return False
    
    async def get_cached_data(self, key: str) -> Any:
        """Get cached data from Redis."""
        
        try:
            data = await self.db_client.get_cache_data(key)
            
            if self.debug_mode and data is not None:
                self.logger.info(f"Retrieved cached data for key: {key}")
            
            return data
            
        except DatabaseError as e:
            self.logger.error(f"Failed to get cached data: {e}")
            return None
    
    async def execute_sql_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute SQL query via database API."""
        
        try:
            result = await self.db_client.execute_postgres_query(
                query=query,
                params=params or {},
                execution_context=self.execution_context
            )
            
            if self.debug_mode:
                self.logger.info(f"SQL query executed successfully, returned {result.get('row_count', 0)} rows")
            
            return result.get('data', [])
            
        except DatabaseError as e:
            self.logger.error(f"SQL query failed: {e}")
            return []
    
    async def create_graph_nodes(self, nodes: List[Dict[str, Any]]) -> bool:
        """Create nodes in Neo4j graph database."""
        
        try:
            for node in nodes:
                query = """
                    CREATE (n:Node {
                        id: $id,
                        type: $type,
                        properties: $properties,
                        user_id: $user_id,
                        execution_id: $execution_id
                    })
                """
                
                params = {
                    "id": node.get("id"),
                    "type": node.get("type", "Default"),
                    "properties": node.get("properties", {}),
                    "user_id": self.execution_context.get("user_id"),
                    "execution_id": self.execution_context.get("execution_id")
                }
                
                await self.db_client.execute_neo4j_query(
                    query=query,
                    params=params,
                    execution_context=self.execution_context
                )
            
            if self.debug_mode:
                self.logger.info(f"Created {len(nodes)} graph nodes")
            
            return True
            
        except DatabaseError as e:
            self.logger.error(f"Failed to create graph nodes: {e}")
            return False
    
    async def query_graph(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Query Neo4j graph database."""
        
        try:
            result = await self.db_client.execute_neo4j_query(
                query=query,
                params=params or {},
                execution_context=self.execution_context
            )
            
            if self.debug_mode:
                self.logger.info(f"Graph query executed successfully")
            
            return result.get('data', [])
            
        except DatabaseError as e:
            self.logger.error(f"Graph query failed: {e}")
            return []
    
    async def index_document(self, document: Dict[str, Any], 
                           index_name: str = "documents") -> bool:
        """Index document in Elasticsearch."""
        
        try:
            # Add processor metadata to document
            document.update({
                "processed_by": self.meta.get('name'),
                "processed_at": datetime.utcnow().isoformat(),
                "execution_id": self.execution_context.get("execution_id")
            })
            
            result = await self.db_client.elasticsearch_index(
                index=index_name,
                document=document
            )
            
            if self.debug_mode:
                self.logger.info(f"Document indexed in: {index_name}")
            
            return result.get('success', False)
            
        except DatabaseError as e:
            self.logger.error(f"Failed to index document: {e}")
            return False
    
    async def get_execution_metadata(self) -> Dict[str, Any]:
        """Get metadata about current execution."""
        
        return {
            "processor_name": self.meta.get('name'),
            "processor_version": self.meta.get('version'),
            "execution_id": self.execution_context.get('execution_id'),
            "user_id": self.execution_context.get('user_id'),
            "pipeline_id": self.execution_context.get('pipeline_id'),
            "step_index": self.execution_context.get('step_index'),
            "debug_mode": self.debug_mode,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def validate_database_access(self) -> Dict[str, bool]:
        """Validate access to different database types."""
        
        validation_results = {}
        
        try:
            # Test PostgreSQL access
            result = await self.db_client.validate_query(
                database_type="postgres",
                operation="SELECT",
                query="SELECT 1"
            )
            validation_results["postgres"] = result.get("valid", False)
        except Exception:
            validation_results["postgres"] = False
        
        try:
            # Test Elasticsearch access
            result = await self.db_client.validate_query(
                database_type="elasticsearch",
                operation="search",
                query=json.dumps({"match_all": {}})
            )
            validation_results["elasticsearch"] = result.get("valid", False)
        except Exception:
            validation_results["elasticsearch"] = False
        
        try:
            # Test Neo4j access
            result = await self.db_client.validate_query(
                database_type="neo4j",
                operation="MATCH",
                query="MATCH (n) RETURN count(n) LIMIT 1"
            )
            validation_results["neo4j"] = result.get("valid", False)
        except Exception:
            validation_results["neo4j"] = False
        
        try:
            # Test Redis access
            result = await self.db_client.validate_query(
                database_type="redis",
                operation="GET",
                query="PING"
            )
            validation_results["redis"] = result.get("valid", False)
        except Exception:
            validation_results["redis"] = False
        
        return validation_results
    
    async def log_processing_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Log processing metrics to database."""
        
        try:
            metrics_data = {
                **metrics,
                "processor_name": self.meta.get('name'),
                "execution_id": self.execution_context.get('execution_id'),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            query = """
                INSERT INTO processor_metrics 
                (processor_name, execution_id, metrics_data, timestamp, user_id)
                VALUES (:processor_name, :execution_id, :metrics_data, :timestamp, :user_id)
            """
            
            params = {
                "processor_name": self.meta.get('name'),
                "execution_id": self.execution_context.get('execution_id'),
                "metrics_data": json.dumps(metrics_data),
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": self.execution_context.get('user_id')
            }
            
            await self.db_client.execute_postgres_query(query, params)
            
            if self.debug_mode:
                self.logger.info("Processing metrics logged successfully")
            
            return True
            
        except DatabaseError as e:
            self.logger.error(f"Failed to log processing metrics: {e}")
            return False


class EnhancedTextProcessor(SandboxAsyncProcessor):
    """Example enhanced text processor using the sandbox database client."""
    
    meta = {
        'name': 'enhanced_text_processor',
        'version': '1.0.0',
        'input_type': 'str',
        'output_type': 'Dict[str, Any]',
        'description': 'Enhanced text processor with database integration'
    }
    
    async def process(self, data: AsyncGenerator[Any, None]) -> AsyncGenerator[Dict[str, Any], None]:
        """Process text data with enhanced features."""
        
        async for text_data in data:
            start_time = datetime.utcnow()
            
            # Process the text
            processed_result = await self._process_text(text_data)
            
            # Save intermediate result
            if self.save_intermediate_results:
                await self.save_intermediate_result(
                    step_name="text_processing",
                    data=processed_result
                )
            
            # Index processed text
            await self.index_document(
                document={
                    "content": processed_result.get("processed_text"),
                    "metadata": processed_result.get("metadata", {}),
                    "original_length": len(str(text_data)),
                    "processed_length": len(processed_result.get("processed_text", ""))
                },
                index_name="processed_texts"
            )
            
            # Log metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            await self.log_processing_metrics({
                "processing_time": processing_time,
                "input_length": len(str(text_data)),
                "output_length": len(processed_result.get("processed_text", "")),
                "status": "completed"
            })
            
            yield processed_result
    
    async def _process_text(self, text: str) -> Dict[str, Any]:
        """Internal text processing logic."""
        
        # Simple text processing example
        processed_text = text.strip().lower()
        word_count = len(text.split())
        char_count = len(text)
        
        # Check cache for similar text
        cache_key = f"text_hash_{hash(text)}"
        cached_result = await self.get_cached_data(cache_key)
        
        if cached_result:
            self.logger.info("Using cached text processing result")
            return cached_result
        
        # Create result
        result = {
            "processed_text": processed_text,
            "metadata": {
                "word_count": word_count,
                "char_count": char_count,
                "processing_timestamp": datetime.utcnow().isoformat()
            },
            "original_text": text
        }
        
        # Cache the result
        await self.cache_data(cache_key, result, ttl=3600)
        
        return result


class EnhancedVectorProcessor(SandboxAsyncProcessor):
    """Example enhanced vector processor with database integration."""
    
    meta = {
        'name': 'enhanced_vector_processor',
        'version': '1.0.0',
        'input_type': 'List[str]',
        'output_type': 'List[Dict[str, Any]]',
        'description': 'Enhanced vector processor with database storage'
    }
    
    async def process(self, data: AsyncGenerator[Any, None]) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """Generate vectors and store them in database."""
        
        async for text_chunks in data:
            vectors = []
            
            for i, chunk in enumerate(text_chunks):
                # Generate fake vector (in real implementation, use actual embedding model)
                import random
                vector = [random.random() for _ in range(384)]  # 384-dimensional vector
                
                vector_data = {
                    "chunk_index": i,
                    "text": chunk,
                    "vector": vector,
                    "vector_dimensions": len(vector),
                    "processing_timestamp": datetime.utcnow().isoformat()
                }
                
                vectors.append(vector_data)
            
            # Store vectors in Elasticsearch
            collection_name = f"execution_{self.execution_context.get('execution_id', 'unknown')}"
            success = await self.store_vectors(vectors, collection_name)
            
            if success and self.debug_mode:
                self.logger.info(f"Successfully stored {len(vectors)} vectors")
            
            # Save processing result
            await self.save_intermediate_result(
                step_name="vector_generation",
                data={
                    "vector_count": len(vectors),
                    "collection_name": collection_name,
                    "success": success
                }
            )
            
            yield vectors


# Factory function for creating sandbox processors
def create_sandbox_processor(processor_class: type, config: Dict[str, Any], 
                           db_client: DatabaseClient) -> SandboxAsyncProcessor:
    """Factory function to create sandbox processors."""
    
    if not issubclass(processor_class, SandboxAsyncProcessor):
        raise ValueError(f"Processor class must inherit from SandboxAsyncProcessor")
    
    return processor_class(config, db_client) 