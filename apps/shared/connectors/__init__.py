from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncIterator
from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class ConnectorType(str, Enum):
    DOCUMENT = "document"
    WEBSOCKET = "websocket"
    API = "api" 
    DATABASE = "database"
    STREAM = "stream"
    FILE_SYSTEM = "file_system"

class DataFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    BINARY = "binary"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"

class ProcessingCapability(str, Enum):
    CHUNK = "chunk"
    EMBED = "embed"
    EXTRACT = "extract"
    TRANSFORM = "transform"
    VALIDATE = "validate"
    ENRICH = "enrich"

class ConnectorConfig(BaseModel):
    """Configuration for a data connector."""
    name: str
    connector_type: ConnectorType
    enabled: bool = True
    config: Dict[str, Any] = {}
    processing_pipeline: List[str] = []
    metadata: Dict[str, Any] = {}

class DataSource(BaseModel):
    """Represents a data source."""
    source_id: str
    source_type: ConnectorType
    format: DataFormat
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None

class ProcessedDocument(BaseModel):
    """Standardized output format from any connector."""
    document_id: str
    source_id: str
    content: str
    metadata: Dict[str, Any] = {}
    format: DataFormat
    chunks: Optional[List[Dict[str, Any]]] = None
    embeddings: Optional[List[List[float]]] = None
    created_at: datetime
    processing_info: Dict[str, Any] = {}

class BaseConnector(ABC):
    """Base class for all data connectors."""
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self.name = config.name
        self.connector_type = config.connector_type
        
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the data source."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection to the data source."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if connection is valid."""
        pass
    
    @abstractmethod
    async def fetch_data(self, source: DataSource, **kwargs) -> AsyncIterator[ProcessedDocument]:
        """Fetch data from the source and yield processed documents."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[DataFormat]:
        """Return list of supported data formats."""
        pass
    
    @abstractmethod
    def get_processing_capabilities(self) -> List[ProcessingCapability]:
        """Return list of processing capabilities."""
        pass
    
    async def validate_config(self) -> bool:
        """Validate connector configuration."""
        return True
    
    async def get_metadata(self, source: DataSource) -> Dict[str, Any]:
        """Get metadata about the data source."""
        return {}

class BaseProcessor(ABC):
    """Base class for data processors."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def process(self, document: ProcessedDocument, **kwargs) -> ProcessedDocument:
        """Process a document and return the processed version."""
        pass
    
    @abstractmethod
    def get_capability(self) -> ProcessingCapability:
        """Return the processing capability this processor provides."""
        pass 