"""
Migration script to add processor and pipeline tables for the Brain_Net application.
Run this script to update the database schema with processor management capabilities.
"""

import asyncio
from sqlalchemy import text
from app.core.database import DatabaseManager
from apps.shared.models import UserProcessor, UserPipeline, PipelineExecution
from sqlmodel import SQLModel

async def migrate_database():
    """Add processor and pipeline tables to the database."""
    db_manager = DatabaseManager()
    
    try:
        # Initialize database connections
        await db_manager.initialize()
        
        # Create tables
        async with db_manager.postgres_engine.begin() as conn:
            # Create the processor, pipeline, and execution tables
            await conn.run_sync(SQLModel.metadata.create_all)
            print("✅ Processor and pipeline tables created successfully")
            
            # Add some sample data
            await add_sample_data(conn)
        
        print("✅ Migration completed!")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        await db_manager.close_all()

async def add_sample_data(conn):
    """Add sample processors and pipelines."""
    try:
        # Sample builtin processors
        sample_processors = [
            {
                'user_id': 1,  # Assuming user with ID 1 exists
                'name': 'Text Chunker',
                'description': 'Splits text into smaller chunks for processing',
                'processor_type': 'builtin',
                'status': 'active',
                'processor_code': '''
from processor_pipeline import AsyncProcessor
from typing import AsyncGenerator, Any, List

class TextChunkerProcessor(AsyncProcessor):
    """Processor that chunks text into smaller pieces."""
    
    meta = {
        "name": "text_chunker",
        "input_type": "str",
        "output_type": "List[str]"
    }
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.chunk_size = config.get('chunk_size', 1000)
        self.overlap = config.get('overlap', 200)
    
    async def process(self, data: AsyncGenerator[Any, None]) -> AsyncGenerator[List[str], None]:
        async for text in data:
            chunks = []
            text_str = str(text)
            
            for i in range(0, len(text_str), self.chunk_size - self.overlap):
                chunk = text_str[i:i + self.chunk_size]
                chunks.append(chunk)
            
            yield chunks
    
    async def after_process(self, input_data: Any, output_data: Any, execution_id: str, step_index: int, *args, **kwargs) -> None:
        """Save chunked data to appropriate storage."""
        print(f"[CHUNKER] Processed {len(output_data)} chunks for execution {execution_id}")
        # TODO: Save chunks to document store or vector database
''',
                'config_schema': '{"type": "object", "properties": {"chunk_size": {"type": "integer", "default": 1000}, "overlap": {"type": "integer", "default": 200}}}',
                'default_config': '{"chunk_size": 1000, "overlap": 200}',
                'input_types': '["str", "text"]',
                'output_types': '["List[str]", "chunks"]',
                'processing_capabilities': '["text_chunking", "text_processing"]',
                'version': '1.0.0',
                'is_template': True
            },
            {
                'user_id': 1,
                'name': 'Vector Generator',
                'description': 'Generates vector embeddings from text chunks',
                'processor_type': 'builtin',
                'status': 'active',
                'processor_code': '''
from processor_pipeline import AsyncProcessor
from typing import AsyncGenerator, Any, Dict, List
import hashlib

class VectorGeneratorProcessor(AsyncProcessor):
    """Processor that generates vectors from text chunks."""
    
    meta = {
        "name": "vector_generator",
        "input_type": "List[str]",
        "output_type": "Dict[str, Any]"
    }
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.vector_size = config.get('vector_size', 128)
        self.model_name = config.get('model_name', 'simple_hash')
    
    async def process(self, data: AsyncGenerator[Any, None]) -> AsyncGenerator[Dict[str, Any], None]:
        async for chunks in data:
            for i, chunk in enumerate(chunks):
                # Simple vector generation (replace with real embedding service)
                vector = [hash(chunk + str(j)) % 1000 / 1000.0 for j in range(self.vector_size)]
                
                yield {
                    "chunk": chunk,
                    "vector": vector,
                    "chunk_index": i,
                    "vector_size": self.vector_size,
                    "model_used": self.model_name
                }
    
    async def after_process(self, input_data: Any, output_data: Any, execution_id: str, step_index: int, *args, **kwargs) -> None:
        """Save vector data to vector database."""
        print(f"[VECTOR] Generated vector for chunk {output_data.get('chunk_index')} in execution {execution_id}")
        # TODO: Save vectors to vector database (Pinecone, Weaviate, etc.)
        # TODO: Save chunk-vector pairs for retrieval
''',
                'config_schema': '{"type": "object", "properties": {"vector_size": {"type": "integer", "default": 128}, "model_name": {"type": "string", "default": "simple_hash"}}}',
                'default_config': '{"vector_size": 128, "model_name": "simple_hash"}',
                'input_types': '["List[str]", "chunks"]',
                'output_types': '["Dict[str, Any]", "vectors"]',
                'processing_capabilities': '["vector_generation", "embedding", "text_analysis"]',
                'version': '1.0.0',
                'is_template': True
            }
        ]
        
        # Insert sample processors
        for processor_data in sample_processors:
            insert_query = """
                INSERT INTO user_processors 
                (user_id, name, description, processor_type, status, processor_code, 
                 config_schema, default_config, input_types, output_types, 
                 processing_capabilities, version, is_template)
                VALUES (%(user_id)s, %(name)s, %(description)s, %(processor_type)s, %(status)s, 
                        %(processor_code)s, %(config_schema)s::jsonb, %(default_config)s::jsonb, 
                        %(input_types)s::jsonb, %(output_types)s::jsonb, 
                        %(processing_capabilities)s::jsonb, %(version)s, %(is_template)s)
                ON CONFLICT (user_id, name) DO NOTHING
            """
            await conn.execute(text(insert_query), processor_data)
        
        print("✅ Sample processors added")
        
        # Sample pipeline
        sample_pipeline = {
            'user_id': 1,
            'name': 'Document Processing Pipeline',
            'description': 'Standard document processing with chunking and vectorization',
            'status': 'active',
            'processor_sequence': '[{"processor_id": 1, "config": {"chunk_size": 1000}, "order": 1}, {"processor_id": 2, "config": {"vector_size": 128}, "order": 2}]',
            'global_config': '{"timeout_seconds": 300, "max_retry_attempts": 3}',
            'parallel_execution': False,
            'max_retry_attempts': 3,
            'version': '1.0.0',
            'is_template': False
        }
        
        # Insert sample pipeline
        pipeline_query = """
            INSERT INTO user_pipelines 
            (user_id, name, description, status, processor_sequence, global_config,
             parallel_execution, max_retry_attempts, version, is_template)
            VALUES (%(user_id)s, %(name)s, %(description)s, %(status)s, 
                    %(processor_sequence)s::jsonb, %(global_config)s::jsonb,
                    %(parallel_execution)s, %(max_retry_attempts)s, %(version)s, %(is_template)s)
            ON CONFLICT (user_id, name) DO NOTHING
        """
        await conn.execute(text(pipeline_query), sample_pipeline)
        
        print("✅ Sample pipeline added")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not add sample data: {str(e)}")
        print("   This is normal if the users table doesn't exist yet")

if __name__ == "__main__":
    print("🚀 Starting processor tables migration...")
    asyncio.run(migrate_database()) 