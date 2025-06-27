"""
Plugin Manager for Data Connectors
Handles dynamic loading, registration, and management of data connectors
"""

import importlib
import inspect
from typing import Dict, List, Type, Optional, Any
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

from . import BaseConnector, BaseProcessor, ConnectorConfig, ConnectorType, ProcessingCapability
from ..database import get_database_manager


class PluginRegistry:
    """Registry for managing available connectors and processors."""
    
    def __init__(self):
        self._connectors: Dict[str, Type[BaseConnector]] = {}
        self._processors: Dict[ProcessingCapability, List[Type[BaseProcessor]]] = {}
        self._configs: Dict[str, ConnectorConfig] = {}
        
    def register_connector(self, name: str, connector_class: Type[BaseConnector]):
        """Register a connector class."""
        if not issubclass(connector_class, BaseConnector):
            raise ValueError(f"Connector {name} must inherit from BaseConnector")
        self._connectors[name] = connector_class
        
    def register_processor(self, processor_class: Type[BaseProcessor]):
        """Register a processor class."""
        if not issubclass(processor_class, BaseProcessor):
            raise ValueError("Processor must inherit from BaseProcessor")
        
        # Create temporary instance to get capability
        temp_instance = processor_class({})
        capability = temp_instance.get_capability()
        
        if capability not in self._processors:
            self._processors[capability] = []
        self._processors[capability].append(processor_class)
        
    def get_connector(self, name: str) -> Optional[Type[BaseConnector]]:
        """Get a connector class by name."""
        return self._connectors.get(name)
        
    def get_processors(self, capability: ProcessingCapability) -> List[Type[BaseProcessor]]:
        """Get all processors for a specific capability."""
        return self._processors.get(capability, [])
        
    def list_connectors(self) -> List[str]:
        """List all registered connector names."""
        return list(self._connectors.keys())
        
    def list_processors(self) -> Dict[ProcessingCapability, int]:
        """List all registered processors by capability."""
        return {cap: len(processors) for cap, processors in self._processors.items()}


class PluginManager:
    """Manages loading, configuration, and execution of data connectors."""
    
    def __init__(self, db_manager=None):
        self.registry = PluginRegistry()
        self.active_connectors: Dict[str, BaseConnector] = {}
        self.db_manager = db_manager or get_database_manager()
        self.executor = ThreadPoolExecutor(max_workers=10)
        
    async def load_plugins(self, plugin_directories: List[str]):
        """Dynamically load plugins from specified directories."""
        for directory in plugin_directories:
            await self._load_plugins_from_directory(directory)
            
    async def _load_plugins_from_directory(self, directory: str):
        """Load plugins from a specific directory."""
        plugin_path = Path(directory)
        if not plugin_path.exists():
            return
            
        for python_file in plugin_path.glob("*.py"):
            if python_file.name.startswith("_"):
                continue
                
            try:
                module_name = python_file.stem
                spec = importlib.util.spec_from_file_location(module_name, python_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Auto-register classes that inherit from BaseConnector or BaseProcessor
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseConnector) and obj != BaseConnector:
                        self.registry.register_connector(name, obj)
                    elif issubclass(obj, BaseProcessor) and obj != BaseProcessor:
                        self.registry.register_processor(obj)
                        
            except Exception as e:
                print(f"Failed to load plugin {python_file}: {e}")
                
    async def create_connector(self, name: str, config: ConnectorConfig) -> Optional[BaseConnector]:
        """Create and configure a connector instance."""
        connector_class = self.registry.get_connector(name)
        if not connector_class:
            raise ValueError(f"Connector {name} not found")
            
        connector = connector_class(config)
        
        # Validate configuration
        if not await connector.validate_config():
            raise ValueError(f"Invalid configuration for connector {name}")
            
        # Test connection
        if not await connector.test_connection():
            raise ConnectionError(f"Cannot connect to data source with connector {name}")
            
        self.active_connectors[config.name] = connector
        return connector
        
    async def get_connector(self, name: str) -> Optional[BaseConnector]:
        """Get an active connector by name."""
        return self.active_connectors.get(name)
        
    async def remove_connector(self, name: str):
        """Remove and disconnect a connector."""
        if name in self.active_connectors:
            await self.active_connectors[name].disconnect()
            del self.active_connectors[name]
            
    async def process_with_pipeline(self, document, pipeline_config: List[str]) -> Any:
        """Process a document through a pipeline of processors."""
        current_doc = document
        
        for processor_name in pipeline_config:
            capability = ProcessingCapability(processor_name)
            processors = self.registry.get_processors(capability)
            
            if not processors:
                continue
                
            # Use the first available processor for this capability
            processor_class = processors[0]
            processor = processor_class(config={})
            current_doc = await processor.process(current_doc)
            
        return current_doc
        
    async def shutdown(self):
        """Shutdown all active connectors."""
        for connector in self.active_connectors.values():
            await connector.disconnect()
        self.active_connectors.clear()
        self.executor.shutdown(wait=True)

# Global plugin manager instance
plugin_manager = PluginManager() 