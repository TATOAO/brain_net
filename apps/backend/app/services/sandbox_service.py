"""
Sandbox Service for Brain_Net Backend
Manages sandbox instances and provides agent-friendly interfaces.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, text
from sqlalchemy.orm import sessionmaker

from app.core.sandbox import (
    PythonSandbox, SandboxManager, SandboxConfig, ExecutionResult, 
    SandboxStatus, DatabaseAccessLayer, SandboxDebugger
)
from app.core.database import get_db_session
from app.core.config import get_settings
from apps.shared.models import User
import logging

logger = logging.getLogger(__name__)


class SandboxService:
    """Service for managing sandbox instances and executions."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.sandbox_manager = SandboxManager(sessionmaker(bind=db_session.bind))
        self.settings = get_settings()
    
    async def create_agent_sandbox(self, user_id: int, config: Dict[str, Any] = None) -> str:
        """Create a new sandbox for an AI agent."""
        try:
            # Create sandbox config
            sandbox_config = SandboxConfig(
                max_execution_time=config.get('max_execution_time', 30),
                max_memory_mb=config.get('max_memory_mb', 256),
                enable_debugging=config.get('enable_debugging', True),
                save_intermediate_results=config.get('save_intermediate_results', True),
                allowed_modules=config.get('allowed_modules', [
                    'json', 'datetime', 'math', 'random', 'collections', 'itertools',
                    'functools', 'operator', 're', 'string', 'uuid', 'hashlib',
                    'base64', 'urllib.parse', 'typing', 'dataclasses', 'enum',
                    'asyncio', 'pandas', 'numpy', 'requests', 'aiohttp'
                ])
            )
            
            # Create sandbox
            sandbox_id = await self.sandbox_manager.create_sandbox(user_id, sandbox_config)
            
            # Log sandbox creation
            logger.info(f"Created sandbox {sandbox_id} for user {user_id}")
            
            return sandbox_id
            
        except Exception as e:
            logger.error(f"Failed to create sandbox for user {user_id}: {e}")
            raise
    
    async def execute_code(self, sandbox_id: str, code: str, context: Dict[str, Any] = None) -> ExecutionResult:
        """Execute Python code in a sandbox."""
        try:
            result = await self.sandbox_manager.execute_in_sandbox(sandbox_id, code, context)
            
            # Log execution
            logger.info(f"Executed code in sandbox {sandbox_id}: {result.status}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute code in sandbox {sandbox_id}: {e}")
            raise
    
    async def debug_code(self, sandbox_id: str, code: str, breakpoints: List[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Debug code execution step by step."""
        try:
            if sandbox_id not in self.sandbox_manager.active_sandboxes:
                raise ValueError(f"Sandbox {sandbox_id} not found")
            
            sandbox = self.sandbox_manager.active_sandboxes[sandbox_id]
            
            # Enhanced debugging with step-by-step execution
            lines = code.split('\n')
            
            for i, line in enumerate(lines):
                if line.strip():  # Skip empty lines
                    # Execute line
                    result = await sandbox.execute_code(line)
                    
                    # Get current state
                    state = sandbox.get_execution_state()
                    
                    yield {
                        'line_number': i + 1,
                        'line_code': line,
                        'result': result,
                        'state': state,
                        'timestamp': datetime.utcnow()
                    }
                    
                    # Stop if there was an error
                    if result.status == SandboxStatus.FAILED:
                        break
                        
        except Exception as e:
            logger.error(f"Failed to debug code in sandbox {sandbox_id}: {e}")
            raise
    
    async def get_sandbox_state(self, sandbox_id: str) -> Dict[str, Any]:
        """Get current state of a sandbox."""
        try:
            state = await self.sandbox_manager.get_sandbox_state(sandbox_id)
            return state
            
        except Exception as e:
            logger.error(f"Failed to get sandbox state {sandbox_id}: {e}")
            raise
    
    async def query_database(self, sandbox_id: str, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a database query through the sandbox."""
        try:
            if sandbox_id not in self.sandbox_manager.active_sandboxes:
                raise ValueError(f"Sandbox {sandbox_id} not found")
            
            sandbox = self.sandbox_manager.active_sandboxes[sandbox_id]
            
            if not sandbox.db_access:
                raise ValueError("Database access not available in this sandbox")
            
            result = await sandbox.db_access.execute_query(query, parameters)
            
            logger.info(f"Database query executed in sandbox {sandbox_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute database query in sandbox {sandbox_id}: {e}")
            raise
    
    async def get_database_schema(self, sandbox_id: str) -> Dict[str, Any]:
        """Get database schema information."""
        try:
            if sandbox_id not in self.sandbox_manager.active_sandboxes:
                raise ValueError(f"Sandbox {sandbox_id} not found")
            
            sandbox = self.sandbox_manager.active_sandboxes[sandbox_id]
            
            if not sandbox.db_access:
                raise ValueError("Database access not available in this sandbox")
            
            # Get tables
            tables = await sandbox.db_access.get_tables()
            
            # Get schema for each table
            schema_info = {}
            for table in tables:
                schema_info[table] = await sandbox.db_access.get_table_schema(table)
            
            return {
                'tables': tables,
                'schema': schema_info,
                'total_tables': len(tables)
            }
            
        except Exception as e:
            logger.error(f"Failed to get database schema in sandbox {sandbox_id}: {e}")
            raise
    
    async def create_processor_template(self, sandbox_id: str, processor_type: str = "data_processor") -> str:
        """Create a processor template for the user to modify."""
        templates = {
            "data_processor": """
from processor_pipeline import AsyncProcessor
from typing import AsyncGenerator, Any, Dict, List
import json

class CustomDataProcessor(AsyncProcessor):
    \"\"\"
    Custom data processor for knowledge base processing.
    
    This processor can be used to transform, analyze, or extract
    information from data in your knowledge base pipeline.
    \"\"\"
    
    meta = {
        "name": "custom_data_processor",
        "input_type": "Any",
        "output_type": "Dict[str, Any]"
    }
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.processing_mode = config.get('processing_mode', 'transform')
        self.output_format = config.get('output_format', 'json')
    
    async def process(self, data: AsyncGenerator[Any, None]) -> AsyncGenerator[Dict[str, Any], None]:
        \"\"\"
        Process the input data.
        
        Args:
            data: Input data stream
            
        Yields:
            Processed data
        \"\"\"
        async for item in data:
            # Debug: inspect the input
            debug(f"Processing item: {type(item)}", "DEBUG")
            inspect_var("current_item", item)
            
            # Example processing logic
            if self.processing_mode == 'transform':
                # Transform the data
                processed_item = await self.transform_data(item)
            elif self.processing_mode == 'analyze':
                # Analyze the data
                processed_item = await self.analyze_data(item)
            else:
                # Default: pass through with metadata
                processed_item = {
                    'original_data': item,
                    'processed_at': str(datetime.utcnow()),
                    'processor_name': self.meta['name']
                }
            
            yield processed_item
    
    async def transform_data(self, data: Any) -> Dict[str, Any]:
        \"\"\"Transform input data.\"\"\"
        # Add your transformation logic here
        # Example: extract key information, reformat, etc.
        
        return {
            'data': data,
            'transformed': True,
            'transformation_type': 'custom'
        }
    
    async def analyze_data(self, data: Any) -> Dict[str, Any]:
        \"\"\"Analyze input data.\"\"\"
        # Add your analysis logic here
        # Example: extract patterns, compute metrics, etc.
        
        return {
            'data': data,
            'analysis': {
                'type': str(type(data)),
                'size': len(str(data)),
                'analyzed_at': str(datetime.utcnow())
            }
        }
    
    async def after_process(self, input_data: Any, output_data: Any, execution_id: str, step_index: int, *args, **kwargs) -> None:
        \"\"\"Called after processing each item.\"\"\"
        debug(f"Processed item {step_index} in execution {execution_id}", "INFO")
        
        # Example: Save to database
        # await db_query(
        #     "INSERT INTO processed_data (execution_id, step_index, data) VALUES (:exec_id, :step, :data)",
        #     {"exec_id": execution_id, "step": step_index, "data": json.dumps(output_data)}
        # )

# Set the result for the processor class
__result__ = CustomDataProcessor
""",
            "text_analyzer": """
from processor_pipeline import AsyncProcessor
from typing import AsyncGenerator, Any, Dict, List
import re
import json

class TextAnalyzerProcessor(AsyncProcessor):
    \"\"\"
    Text analysis processor for knowledge base content.
    
    Analyzes text content and extracts meaningful information
    such as keywords, entities, sentiment, etc.
    \"\"\"
    
    meta = {
        "name": "text_analyzer",
        "input_type": "str",
        "output_type": "Dict[str, Any]"
    }
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.extract_entities = config.get('extract_entities', True)
        self.extract_keywords = config.get('extract_keywords', True)
        self.min_keyword_length = config.get('min_keyword_length', 3)
    
    async def process(self, data: AsyncGenerator[Any, None]) -> AsyncGenerator[Dict[str, Any], None]:
        \"\"\"Process text data and extract insights.\"\"\"
        async for text_data in data:
            # Convert to string if needed
            text = str(text_data) if not isinstance(text_data, str) else text_data
            
            debug(f"Analyzing text of length: {len(text)}", "INFO")
            
            # Perform analysis
            analysis = {
                'original_text': text,
                'statistics': await self.get_text_statistics(text),
                'processed_at': str(datetime.utcnow())
            }
            
            if self.extract_keywords:
                analysis['keywords'] = await self.extract_keywords_from_text(text)
            
            if self.extract_entities:
                analysis['entities'] = await self.extract_entities_from_text(text)
            
            yield analysis
    
    async def get_text_statistics(self, text: str) -> Dict[str, Any]:
        \"\"\"Get basic text statistics.\"\"\"
        words = text.split()
        sentences = text.split('.')
        
        return {
            'character_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0
        }
    
    async def extract_keywords_from_text(self, text: str) -> List[str]:
        \"\"\"Extract keywords from text.\"\"\"
        # Simple keyword extraction (you can enhance this)
        words = re.findall(r'\\b\\w+\\b', text.lower())
        
        # Filter words by length and common stop words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        
        keywords = [word for word in words 
                   if len(word) >= self.min_keyword_length and word not in stop_words]
        
        # Return most frequent keywords
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        return sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:20]
    
    async def extract_entities_from_text(self, text: str) -> List[Dict[str, Any]]:
        \"\"\"Extract entities from text (simple implementation).\"\"\"
        entities = []
        
        # Simple email extraction
        emails = re.findall(r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b', text)
        for email in emails:
            entities.append({'type': 'email', 'value': email})
        
        # Simple URL extraction
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        for url in urls:
            entities.append({'type': 'url', 'value': url})
        
        # Simple phone number extraction
        phones = re.findall(r'\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b', text)
        for phone in phones:
            entities.append({'type': 'phone', 'value': phone})
        
        return entities

# Set the result for the processor class
__result__ = TextAnalyzerProcessor
""",
            "database_connector": """
from processor_pipeline import AsyncProcessor
from typing import AsyncGenerator, Any, Dict, List
import json

class DatabaseConnectorProcessor(AsyncProcessor):
    \"\"\"
    Database connector processor for knowledge base operations.
    
    Connects to databases, executes queries, and manages data
    persistence for the knowledge base pipeline.
    \"\"\"
    
    meta = {
        "name": "database_connector",
        "input_type": "Dict[str, Any]",
        "output_type": "Dict[str, Any]"
    }
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.table_name = config.get('table_name', 'knowledge_data')
        self.operation = config.get('operation', 'insert')  # insert, select, update
        self.batch_size = config.get('batch_size', 100)
    
    async def process(self, data: AsyncGenerator[Any, None]) -> AsyncGenerator[Dict[str, Any], None]:
        \"\"\"Process data with database operations.\"\"\"
        
        # First, let's check what tables are available
        tables = await db_tables()
        debug(f"Available tables: {tables}", "INFO")
        
        # Get schema for our target table if it exists
        if self.table_name in tables:
            schema = await db_schema(self.table_name)
            debug(f"Table schema for {self.table_name}: {schema}", "INFO")
        
        batch = []
        batch_count = 0
        
        async for item in data:
            batch.append(item)
            
            # Process batch when it reaches batch_size
            if len(batch) >= self.batch_size:
                result = await self.process_batch(batch)
                batch = []
                batch_count += 1
                
                yield {
                    'batch_number': batch_count,
                    'items_processed': len(batch),
                    'operation': self.operation,
                    'result': result
                }
        
        # Process remaining items
        if batch:
            result = await self.process_batch(batch)
            batch_count += 1
            
            yield {
                'batch_number': batch_count,
                'items_processed': len(batch),
                'operation': self.operation,
                'result': result,
                'final_batch': True
            }
    
    async def process_batch(self, batch: List[Any]) -> Dict[str, Any]:
        \"\"\"Process a batch of items.\"\"\"
        
        if self.operation == 'insert':
            return await self.insert_batch(batch)
        elif self.operation == 'select':
            return await self.select_batch(batch)
        elif self.operation == 'update':
            return await self.update_batch(batch)
        else:
            return {'error': f'Unknown operation: {self.operation}'}
    
    async def insert_batch(self, batch: List[Any]) -> Dict[str, Any]:
        \"\"\"Insert batch of data into database.\"\"\"
        try:
            # Example: Insert processed data
            for item in batch:
                query = f\"\"\"
                    INSERT INTO {self.table_name} (data, created_at) 
                    VALUES (:data, NOW())
                \"\"\"
                await db_query(query, {'data': json.dumps(item)})
            
            return {'status': 'success', 'inserted_count': len(batch)}
            
        except Exception as e:
            debug(f"Insert batch failed: {e}", "ERROR")
            return {'status': 'error', 'error': str(e)}
    
    async def select_batch(self, batch: List[Any]) -> Dict[str, Any]:
        \"\"\"Select data from database based on batch criteria.\"\"\"
        try:
            # Example: Select data based on batch criteria
            results = []
            for item in batch:
                # Assuming item has an 'id' field
                item_id = item.get('id') if isinstance(item, dict) else str(item)
                query = f\"SELECT * FROM {self.table_name} WHERE id = :id\"
                result = await db_query(query, {'id': item_id})
                results.extend(result)
            
            return {'status': 'success', 'results': results, 'count': len(results)}
            
        except Exception as e:
            debug(f"Select batch failed: {e}", "ERROR")
            return {'status': 'error', 'error': str(e)}
    
    async def update_batch(self, batch: List[Any]) -> Dict[str, Any]:
        \"\"\"Update batch of data in database.\"\"\"
        try:
            updated_count = 0
            for item in batch:
                if isinstance(item, dict) and 'id' in item:
                    query = f\"\"\"
                        UPDATE {self.table_name} 
                        SET data = :data, updated_at = NOW()
                        WHERE id = :id
                    \"\"\"
                    result = await db_query(query, {
                        'id': item['id'],
                        'data': json.dumps(item)
                    })
                    updated_count += 1
            
            return {'status': 'success', 'updated_count': updated_count}
            
        except Exception as e:
            debug(f"Update batch failed: {e}", "ERROR")
            return {'status': 'error', 'error': str(e)}

# Set the result for the processor class
__result__ = DatabaseConnectorProcessor
"""
        }
        
        template = templates.get(processor_type, templates["data_processor"])
        
        # Execute the template in the sandbox to validate it
        result = await self.execute_code(sandbox_id, template)
        
        if result.status == SandboxStatus.COMPLETED:
            return template
        else:
            raise ValueError(f"Template validation failed: {result.error}")
    
    async def get_execution_history(self, sandbox_id: str) -> List[ExecutionResult]:
        """Get execution history for a sandbox."""
        try:
            history = self.sandbox_manager.get_execution_history()
            
            # Filter by sandbox_id if needed
            filtered_history = [
                result for result in history 
                if result.execution_id.startswith(sandbox_id[:8])  # Match first 8 chars
            ]
            
            return filtered_history
            
        except Exception as e:
            logger.error(f"Failed to get execution history: {e}")
            raise
    
    async def cleanup_sandbox(self, sandbox_id: str):
        """Clean up a specific sandbox."""
        try:
            await self.sandbox_manager.cleanup_sandbox(sandbox_id)
            logger.info(f"Cleaned up sandbox {sandbox_id}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup sandbox {sandbox_id}: {e}")
            raise
    
    async def cleanup_all_sandboxes(self):
        """Clean up all active sandboxes."""
        try:
            await self.sandbox_manager.cleanup_all()
            logger.info("Cleaned up all sandboxes")
            
        except Exception as e:
            logger.error(f"Failed to cleanup all sandboxes: {e}")
            raise
    
    async def get_sandbox_statistics(self) -> Dict[str, Any]:
        """Get statistics about sandbox usage."""
        try:
            active_sandboxes = len(self.sandbox_manager.active_sandboxes)
            execution_history = self.sandbox_manager.get_execution_history()
            
            # Calculate statistics
            total_executions = len(execution_history)
            successful_executions = len([r for r in execution_history if r.status == SandboxStatus.COMPLETED])
            failed_executions = len([r for r in execution_history if r.status == SandboxStatus.FAILED])
            
            avg_execution_time = sum(r.execution_time for r in execution_history) / total_executions if total_executions > 0 else 0
            
            return {
                'active_sandboxes': active_sandboxes,
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                'average_execution_time': avg_execution_time,
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to get sandbox statistics: {e}")
            raise


# Dependency injection for FastAPI
async def get_sandbox_service(db: AsyncSession = None) -> SandboxService:
    """Get sandbox service instance."""
    if db is None:
        db = await get_db_session()
    return SandboxService(db) 