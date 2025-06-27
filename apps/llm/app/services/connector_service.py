"""
Connector Service for LLM Application
Integrates the plugin system with the existing LLM service
"""

import asyncio
from typing import List, Dict, Any, Optional, AsyncIterator
from datetime import datetime

from app.core.database import DatabaseManager
from app.core.logging import LLMLogger
from app.services.rag import RAGService
from ...shared.connectors import (
    plugin_manager, config_manager, 
    BaseConnector, ConnectorConfig, DataSource, ProcessedDocument, ConnectorType
)

logger = LLMLogger("connector_service")


class ConnectorService:
    """Service for managing data connectors in the LLM application."""
    
    def __init__(self, db_manager: DatabaseManager, rag_service: Optional[RAGService] = None):
        self.db_manager = db_manager
        self.rag_service = rag_service
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
    async def initialize(self):
        """Initialize the connector service."""
        try:
            # Load plugins from the plugins directory
            plugin_directories = [
                "apps/shared/connectors/examples",
                "plugins/custom",  # For user-defined plugins
                "plugins/community"  # For community plugins
            ]
            
            await plugin_manager.load_plugins(plugin_directories)
            logger.info(f"Loaded connectors: {plugin_manager.registry.list_connectors()}")
            
            # Load all configuration files
            configs = config_manager.load_all_configs()
            logger.info(f"Loaded {len(configs)} connector configurations")
            
            # Start enabled connectors
            for config in configs:
                if config.enabled:
                    await self.start_connector(config)
                    
        except Exception as e:
            logger.error(f"Failed to initialize connector service: {e}")
            
    async def start_connector(self, config: ConnectorConfig) -> bool:
        """Start a data connector."""
        try:
            # Validate configuration
            errors = config_manager.validate_config(config)
            if errors:
                logger.error(f"Configuration errors for {config.name}: {errors}")
                return False
                
            # Create connector instance
            connector = await plugin_manager.create_connector(config.name, config)
            
            # Create data source
            data_source = DataSource(
                source_id=f"{config.name}_{datetime.now().timestamp()}",
                source_type=config.connector_type,
                format=self._infer_data_format(config),
                metadata=config.metadata,
                created_at=datetime.now()
            )
            
            # Start data processing task
            task_name = f"connector_{config.name}"
            if task_name not in self.active_tasks:
                task = asyncio.create_task(
                    self._process_connector_data(connector, data_source, config)
                )
                self.active_tasks[task_name] = task
                logger.info(f"Started connector: {config.name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to start connector {config.name}: {e}")
            return False
            
    async def stop_connector(self, connector_name: str) -> bool:
        """Stop a data connector."""
        try:
            task_name = f"connector_{connector_name}"
            if task_name in self.active_tasks:
                self.active_tasks[task_name].cancel()
                del self.active_tasks[task_name]
                
            await plugin_manager.remove_connector(connector_name)
            logger.info(f"Stopped connector: {connector_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop connector {connector_name}: {e}")
            return False
            
    async def _process_connector_data(self, connector: BaseConnector, source: DataSource, config: ConnectorConfig):
        """Process data from a connector continuously."""
        try:
            async for document in connector.fetch_data(source):
                # Process document through the pipeline
                processed_doc = await plugin_manager.process_with_pipeline(
                    document, config.processing_pipeline
                )
                
                # Store in knowledge base
                await self._store_document(processed_doc)
                
                # Add to RAG system if available
                if self.rag_service:
                    await self._add_to_rag(processed_doc)
                    
                logger.debug(f"Processed document: {processed_doc.document_id}")
                
        except asyncio.CancelledError:
            logger.info(f"Connector task cancelled: {config.name}")
        except Exception as e:
            logger.error(f"Error processing data from {config.name}: {e}")
            
    async def _store_document(self, document: ProcessedDocument) -> bool:
        """Store processed document in the database."""
        try:
            # Store in PostgreSQL for metadata
            query = """
            INSERT INTO processed_documents 
            (document_id, source_id, content, metadata, format, created_at, processing_info)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (document_id) DO UPDATE SET
                content = EXCLUDED.content,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            """
            
            await self.db_manager.execute_query(
                query,
                document.document_id,
                document.source_id,
                document.content,
                document.metadata,
                document.format.value,
                document.created_at,
                document.processing_info
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store document {document.document_id}: {e}")
            return False
            
    async def _add_to_rag(self, document: ProcessedDocument) -> bool:
        """Add document to RAG system."""
        try:
            if not self.rag_service:
                return False
                
            # Generate embeddings if not already present
            if not document.embeddings:
                # This would call your existing embedding service
                embeddings = await self.rag_service.generate_embeddings(document.content)
                document.embeddings = embeddings
                
            # Add to vector store
            await self.rag_service.add_document(
                document_id=document.document_id,
                content=document.content,
                embeddings=document.embeddings,
                metadata=document.metadata
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document to RAG: {e}")
            return False
            
    def _infer_data_format(self, config: ConnectorConfig):
        """Infer data format from connector configuration."""
        from ...shared.connectors import DataFormat
        
        if config.connector_type == ConnectorType.WEBSOCKET:
            return DataFormat.JSON
        elif config.connector_type == ConnectorType.API:
            return DataFormat.JSON
        elif config.connector_type == ConnectorType.FILE_SYSTEM:
            return DataFormat.TEXT
        else:
            return DataFormat.TEXT
            
    async def get_connector_status(self) -> Dict[str, Any]:
        """Get status of all connectors."""
        status = {
            "active_connectors": len(self.active_tasks),
            "available_connectors": plugin_manager.registry.list_connectors(),
            "available_processors": plugin_manager.registry.list_processors(),
            "active_tasks": list(self.active_tasks.keys())
        }
        return status
        
    async def create_connector_from_template(self, template_name: str, custom_config: Dict[str, Any]) -> str:
        """Create a new connector configuration from a template."""
        try:
            # Create configuration file from template
            config_file = config_manager.create_config_file(template_name)
            
            # Load and modify with custom configuration
            config = config_manager.load_config_file(config_file)
            
            # Update with custom settings
            config.config.update(custom_config)
            
            # Save updated configuration
            updated_file = config_manager.save_config(config)
            
            # Start the connector if enabled
            if config.enabled:
                await self.start_connector(config)
                
            return updated_file
            
        except Exception as e:
            logger.error(f"Failed to create connector from template: {e}")
            raise
            
    async def shutdown(self):
        """Shutdown all connectors."""
        logger.info("Shutting down connector service...")
        
        # Cancel all active tasks
        for task in self.active_tasks.values():
            task.cancel()
            
        # Wait for tasks to complete
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
            
        # Shutdown plugin manager
        await plugin_manager.shutdown()
        
        logger.info("Connector service shutdown complete") 