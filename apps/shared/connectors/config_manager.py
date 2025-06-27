"""
Configuration Manager for Data Connectors
Handles plugin configuration loading, validation, and management
"""

import yaml
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

from . import ConnectorConfig, ConnectorType
from .plugin_manager import plugin_manager


class ConfigManager:
    """Manages plugin configurations and templates."""
    
    def __init__(self, config_dir: str = "configs/connectors"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.active_configs: Dict[str, ConnectorConfig] = {}
        
    def load_config_templates(self) -> Dict[str, Any]:
        """Load configuration templates for all connector types."""
        templates = {
            "websocket_news": {
                "name": "websocket_news_feed",
                "connector_type": "websocket",
                "enabled": True,
                "config": {
                    "websocket_url": "wss://api.example.com/news",
                    "headers": {
                        "Authorization": "Bearer YOUR_API_KEY"
                    },
                    "subscribe_message": {
                        "action": "subscribe",
                        "channels": ["news"]
                    }
                },
                "processing_pipeline": ["extract", "chunk", "embed"],
                "metadata": {
                    "description": "Real-time news feed connector",
                    "category": "news",
                    "update_frequency": "real-time"
                }
            },
            "financial_market": {
                "name": "stock_market_data",
                "connector_type": "api",
                "enabled": True,
                "config": {
                    "api_key": "YOUR_FINANCIAL_API_KEY",
                    "base_url": "https://api.financialdata.com",
                    "symbols": ["AAPL", "GOOGL", "MSFT"],
                    "data_types": ["price", "news", "fundamentals"],
                    "update_interval": 60
                },
                "processing_pipeline": ["extract", "transform", "enrich", "embed"],
                "metadata": {
                    "description": "Stock market data and news connector",
                    "category": "financial",
                    "update_frequency": "1-minute"
                }
            },
            "document_upload": {
                "name": "document_processor",
                "connector_type": "file_system",
                "enabled": True,
                "config": {
                    "upload_directory": "/app/uploads",
                    "supported_formats": ["pdf", "docx", "txt", "md"],
                    "max_file_size": "50MB",
                    "auto_process": True
                },
                "processing_pipeline": ["extract", "chunk", "embed"],
                "metadata": {
                    "description": "Document upload and processing connector",
                    "category": "documents",
                    "update_frequency": "on-upload"
                }
            },
            "user_conversations": {
                "name": "conversation_memory",
                "connector_type": "database",
                "enabled": True,
                "config": {
                    "database_url": "postgresql://user:pass@localhost/conversations",
                    "table_name": "user_conversations",
                    "retention_days": 365,
                    "include_metadata": True
                },
                "processing_pipeline": ["extract", "chunk", "embed"],
                "metadata": {
                    "description": "User conversation history connector",
                    "category": "conversations",
                    "update_frequency": "continuous"
                }
            },
            "custom_api": {
                "name": "custom_api_connector",
                "connector_type": "api",
                "enabled": False,
                "config": {
                    "base_url": "https://api.yourservice.com",
                    "api_key": "YOUR_API_KEY",
                    "endpoints": {
                        "data": "/v1/data",
                        "health": "/v1/health"
                    },
                    "headers": {},
                    "params": {},
                    "rate_limit": 100
                },
                "processing_pipeline": ["extract", "transform", "embed"],
                "metadata": {
                    "description": "Custom API data connector template",
                    "category": "custom",
                    "update_frequency": "configurable"
                }
            }
        }
        return templates
        
    def create_config_file(self, template_name: str, output_file: Optional[str] = None) -> str:
        """Create a configuration file from a template."""
        templates = self.load_config_templates()
        
        if template_name not in templates:
            raise ValueError(f"Template '{template_name}' not found")
            
        template = templates[template_name]
        
        if output_file is None:
            output_file = f"{template_name}_config.yaml"
            
        config_path = self.config_dir / output_file
        
        with open(config_path, 'w') as f:
            yaml.dump(template, f, default_flow_style=False, indent=2)
            
        return str(config_path)
        
    def load_config_file(self, config_file: str) -> ConnectorConfig:
        """Load configuration from YAML file."""
        config_path = Path(config_file)
        if not config_path.is_absolute():
            config_path = self.config_dir / config_path
            
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            
        # Convert to ConnectorConfig object
        connector_config = ConnectorConfig(
            name=config_data['name'],
            connector_type=ConnectorType(config_data['connector_type']),
            enabled=config_data.get('enabled', True),
            config=config_data.get('config', {}),
            processing_pipeline=config_data.get('processing_pipeline', []),
            metadata=config_data.get('metadata', {})
        )
        
        self.active_configs[connector_config.name] = connector_config
        return connector_config
        
    def load_all_configs(self) -> List[ConnectorConfig]:
        """Load all configuration files from the config directory."""
        configs = []
        
        for config_file in self.config_dir.glob("*.yaml"):
            try:
                config = self.load_config_file(str(config_file))
                configs.append(config)
            except Exception as e:
                print(f"Failed to load config {config_file}: {e}")
                
        return configs
        
    def validate_config(self, config: ConnectorConfig) -> List[str]:
        """Validate a connector configuration."""
        errors = []
        
        # Check if connector type is supported
        if config.connector_type not in ConnectorType:
            errors.append(f"Unsupported connector type: {config.connector_type}")
            
        # Check if connector class exists
        connector_class = plugin_manager.registry.get_connector(config.name)
        if not connector_class:
            errors.append(f"Connector class not found for: {config.name}")
            
        # Validate required configuration keys
        required_keys = self._get_required_config_keys(config.connector_type)
        for key in required_keys:
            if key not in config.config:
                errors.append(f"Missing required configuration key: {key}")
                
        return errors
        
    def _get_required_config_keys(self, connector_type: ConnectorType) -> List[str]:
        """Get required configuration keys for a connector type."""
        required_keys = {
            ConnectorType.WEBSOCKET: ["websocket_url"],
            ConnectorType.API: ["base_url", "api_key"],
            ConnectorType.DATABASE: ["database_url"],
            ConnectorType.FILE_SYSTEM: ["upload_directory"],
            ConnectorType.STREAM: ["stream_config"]
        }
        return required_keys.get(connector_type, [])
        
    def get_active_configs(self) -> Dict[str, ConnectorConfig]:
        """Get all active configurations."""
        return self.active_configs.copy()
        
    def save_config(self, config: ConnectorConfig, filename: Optional[str] = None) -> str:
        """Save a configuration to file."""
        if filename is None:
            filename = f"{config.name}_config.yaml"
            
        config_path = self.config_dir / filename
        
        config_dict = {
            "name": config.name,
            "connector_type": config.connector_type.value,
            "enabled": config.enabled,
            "config": config.config,
            "processing_pipeline": config.processing_pipeline,
            "metadata": config.metadata
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
        return str(config_path)

# Global config manager instance
config_manager = ConfigManager() 