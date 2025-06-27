"""
Financial Market Data Connector
Example implementation for stock market data feeds
"""

import asyncio
import aiohttp
from typing import AsyncIterator, List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

from .. import BaseConnector, ConnectorConfig, DataSource, ProcessedDocument, ConnectorType, DataFormat, ProcessingCapability


class FinancialMarketConnector(BaseConnector):
    """Connector for financial market data (stocks, crypto, etc.)."""
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.session = None
        self.api_key = self.config.config.get("api_key")
        self.base_url = self.config.config.get("base_url", "https://api.example.com")
        
    async def connect(self) -> bool:
        """Initialize HTTP session."""
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return True
        
    async def disconnect(self) -> bool:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
        return True
        
    async def test_connection(self) -> bool:
        """Test API connection."""
        if not self.session:
            await self.connect()
            
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except:
            return False
            
    async def fetch_data(self, source: DataSource, **kwargs) -> AsyncIterator[ProcessedDocument]:
        """Fetch financial market data."""
        if not self.session:
            await self.connect()
            
        symbols = kwargs.get("symbols", ["AAPL", "GOOGL", "MSFT"])
        data_type = kwargs.get("data_type", "price")  # price, news, fundamentals
        
        if data_type == "price":
            async for doc in self._fetch_price_data(source, symbols):
                yield doc
        elif data_type == "news":
            async for doc in self._fetch_news_data(source, symbols):
                yield doc
        elif data_type == "fundamentals":
            async for doc in self._fetch_fundamental_data(source, symbols):
                yield doc
                
    async def _fetch_price_data(self, source: DataSource, symbols: List[str]) -> AsyncIterator[ProcessedDocument]:
        """Fetch real-time price data."""
        for symbol in symbols:
            try:
                url = f"{self.base_url}/v1/quote"
                params = {"symbol": symbol}
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        content = self._format_price_content(symbol, data)
                        
                        doc = ProcessedDocument(
                            document_id=f"price_{symbol}_{datetime.now().timestamp()}",
                            source_id=source.source_id,
                            content=content,
                            metadata={
                                "symbol": symbol,
                                "price": data.get("price", 0),
                                "change": data.get("change", 0),
                                "change_percent": data.get("change_percent", 0),
                                "volume": data.get("volume", 0),
                                "market_cap": data.get("market_cap", 0),
                                "timestamp": data.get("timestamp", ""),
                                "exchange": data.get("exchange", ""),
                                "currency": data.get("currency", "USD"),
                                "data_type": "price",
                                "raw_data": data
                            },
                            format=DataFormat.JSON,
                            created_at=datetime.now(),
                            processing_info={"connector": "FinancialMarketConnector", "type": "price"}
                        )
                        
                        yield doc
                        
            except Exception as e:
                print(f"Error fetching price data for {symbol}: {e}")
                
    async def _fetch_news_data(self, source: DataSource, symbols: List[str]) -> AsyncIterator[ProcessedDocument]:
        """Fetch financial news related to symbols."""
        for symbol in symbols:
            try:
                url = f"{self.base_url}/v1/news"
                params = {"symbol": symbol, "limit": 10}
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        news_data = await response.json()
                        
                        for article in news_data.get("articles", []):
                            content = self._format_news_content(symbol, article)
                            
                            doc = ProcessedDocument(
                                document_id=f"news_{symbol}_{article.get('id', datetime.now().timestamp())}",
                                source_id=source.source_id,
                                content=content,
                                metadata={
                                    "symbol": symbol,
                                    "headline": article.get("headline", ""),
                                    "summary": article.get("summary", ""),
                                    "author": article.get("author", ""),
                                    "published_at": article.get("published_at", ""),
                                    "sentiment": article.get("sentiment", "neutral"),
                                    "url": article.get("url", ""),
                                    "source": article.get("source", ""),
                                    "data_type": "news",
                                    "raw_data": article
                                },
                                format=DataFormat.TEXT,
                                created_at=datetime.now(),
                                processing_info={"connector": "FinancialMarketConnector", "type": "news"}
                            )
                            
                            yield doc
                            
            except Exception as e:
                print(f"Error fetching news data for {symbol}: {e}")
                
    def _format_price_content(self, symbol: str, data: Dict[str, Any]) -> str:
        """Format price data as readable content."""
        content_parts = [
            f"Stock: {symbol}",
            f"Current Price: ${data.get('price', 'N/A')}",
            f"Change: {data.get('change', 'N/A')} ({data.get('change_percent', 'N/A')}%)",
            f"Volume: {data.get('volume', 'N/A'):,}",
            f"Market Cap: ${data.get('market_cap', 'N/A'):,}",
            f"Exchange: {data.get('exchange', 'N/A')}",
            f"Last Updated: {data.get('timestamp', 'N/A')}"
        ]
        return "\n".join(content_parts)
        
    def _format_news_content(self, symbol: str, article: Dict[str, Any]) -> str:
        """Format news article as readable content."""
        content_parts = [
            f"Stock: {symbol}",
            f"Headline: {article.get('headline', '')}",
            f"Summary: {article.get('summary', '')}",
            f"Author: {article.get('author', 'Unknown')}",
            f"Published: {article.get('published_at', '')}",
            f"Sentiment: {article.get('sentiment', 'neutral').title()}"
        ]
        return "\n\n".join(content_parts)
        
    def get_supported_formats(self) -> List[DataFormat]:
        """Return supported data formats."""
        return [DataFormat.JSON, DataFormat.TEXT, DataFormat.CSV]
        
    def get_processing_capabilities(self) -> List[ProcessingCapability]:
        """Return processing capabilities."""
        return [ProcessingCapability.EXTRACT, ProcessingCapability.TRANSFORM, ProcessingCapability.ENRICH]
        
    async def validate_config(self) -> bool:
        """Validate connector configuration."""
        required_keys = ["api_key", "base_url"]
        return all(key in self.config.config for key in required_keys) 