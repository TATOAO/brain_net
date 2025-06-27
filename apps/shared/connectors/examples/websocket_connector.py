"""
WebSocket News Connector
Example implementation for real-time news feeds
"""

import asyncio
import websockets
import json
from typing import AsyncIterator, List, Dict, Any
from datetime import datetime

from .. import BaseConnector, ConnectorConfig, DataSource, ProcessedDocument, ConnectorType, DataFormat, ProcessingCapability


class WebSocketNewsConnector(BaseConnector):
    """Connector for real-time news feeds via WebSocket."""
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.websocket = None
        self.is_connected = False
        
    async def connect(self) -> bool:
        """Connect to WebSocket news feed."""
        try:
            ws_url = self.config.config.get("websocket_url")
            headers = self.config.config.get("headers", {})
            
            self.websocket = await websockets.connect(ws_url, extra_headers=headers)
            self.is_connected = True
            return True
        except Exception as e:
            print(f"WebSocket connection failed: {e}")
            return False
            
    async def disconnect(self) -> bool:
        """Disconnect from WebSocket."""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
        return True
        
    async def test_connection(self) -> bool:
        """Test WebSocket connection."""
        if not self.is_connected:
            return await self.connect()
        return True
        
    async def fetch_data(self, source: DataSource, **kwargs) -> AsyncIterator[ProcessedDocument]:
        """Fetch real-time news data from WebSocket."""
        if not self.is_connected:
            await self.connect()
            
        try:
            # Subscribe to news feed
            subscribe_msg = self.config.config.get("subscribe_message", {})
            if subscribe_msg:
                await self.websocket.send(json.dumps(subscribe_msg))
                
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    
                    # Transform news data to ProcessedDocument
                    doc = ProcessedDocument(
                        document_id=f"news_{data.get('id', datetime.now().timestamp())}",
                        source_id=source.source_id,
                        content=self._extract_content(data),
                        metadata={
                            "title": data.get("title", ""),
                            "author": data.get("author", ""),
                            "published_at": data.get("published_at", ""),
                            "category": data.get("category", ""),
                            "sentiment": data.get("sentiment", ""),
                            "url": data.get("url", ""),
                            "raw_data": data
                        },
                        format=DataFormat.JSON,
                        created_at=datetime.now(),
                        processing_info={"connector": "WebSocketNewsConnector"}
                    )
                    
                    yield doc
                    
                except json.JSONDecodeError:
                    continue
                    
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
            self.is_connected = False
            
    def _extract_content(self, data: Dict[str, Any]) -> str:
        """Extract main content from news data."""
        content_parts = []
        
        if "title" in data:
            content_parts.append(f"Title: {data['title']}")
        if "summary" in data:
            content_parts.append(f"Summary: {data['summary']}")
        if "body" in data:
            content_parts.append(f"Body: {data['body']}")
            
        return "\n\n".join(content_parts)
        
    def get_supported_formats(self) -> List[DataFormat]:
        """Return supported data formats."""
        return [DataFormat.JSON, DataFormat.TEXT]
        
    def get_processing_capabilities(self) -> List[ProcessingCapability]:
        """Return processing capabilities."""
        return [ProcessingCapability.EXTRACT, ProcessingCapability.TRANSFORM]
        
    async def validate_config(self) -> bool:
        """Validate connector configuration."""
        required_keys = ["websocket_url"]
        return all(key in self.config.config for key in required_keys) 