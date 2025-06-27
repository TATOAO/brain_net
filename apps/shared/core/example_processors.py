"""
Example implementations of document processors.

These serve as reference implementations and can be used as starting points
for creating custom processors.
"""

import re
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from .processor import (
    BaseChunker, BaseNERProcessor, BaseDocumentProcessor,
    ProcessorConfig, ProcessingType, DocumentFormat, DocumentChunk,
    ProcessedDocument, ProcessingContext, ProcessingResult, ProcessingStatus
)


class FixedSizeChunker(BaseChunker):
    """
    Simple chunker that splits text into fixed-size chunks with overlap.
    """
    
    def __init__(self, config: ProcessorConfig = None):
        if config is None:
            config = ProcessorConfig(
                processor_id="fixed_size_chunker",
                processing_type=ProcessingType.CHUNKING,
                name="Fixed Size Chunker",
                description="Splits text into chunks of fixed character size with configurable overlap"
            )
        super().__init__(config)
    
    def get_supported_formats(self) -> List[DocumentFormat]:
        return [DocumentFormat.TEXT, DocumentFormat.MARKDOWN, DocumentFormat.HTML]
    
    def get_required_parameters(self) -> Dict[str, Any]:
        return {"chunk_size": {"type": "int", "description": "Maximum characters per chunk"}}
    
    def get_optional_parameters(self) -> Dict[str, Any]:
        return {"overlap": {"type": "int", "description": "Character overlap between chunks", "default": 200}}
    
    async def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200, **kwargs) -> List[DocumentChunk]:
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_content = text[start:end].strip()
            
            if chunk_content:
                chunk = DocumentChunk(
                    chunk_id=f"chunk_{chunk_index}_{uuid.uuid4().hex[:8]}",
                    document_id="",
                    content=chunk_content,
                    start_pos=start,
                    end_pos=end,
                    metadata={"chunk_index": chunk_index, "chunk_method": "fixed_size"}
                )
                chunks.append(chunk)
                chunk_index += 1
            
            start = max(start + 1, end - overlap)
            if start >= end:
                start = end
        
        return chunks


class SentenceBasedChunker(BaseChunker):
    """
    Chunker that splits text into chunks based on sentence boundaries.
    """
    
    def __init__(self, config: ProcessorConfig = None):
        if config is None:
            config = ProcessorConfig(
                processor_id="sentence_chunker",
                processing_type=ProcessingType.CHUNKING,
                name="Sentence-Based Chunker",
                description="Splits text into chunks respecting sentence boundaries",
                parameters={
                    "max_sentences": 10,
                    "max_chunk_size": 2000
                }
            )
        super().__init__(config)
    
    def get_supported_formats(self) -> List[DocumentFormat]:
        return [
            DocumentFormat.TEXT,
            DocumentFormat.MARKDOWN,
            DocumentFormat.HTML
        ]
    
    def get_required_parameters(self) -> Dict[str, Any]:
        return {}
    
    def get_optional_parameters(self) -> Dict[str, Any]:
        return {
            "max_sentences": {
                "type": "int",
                "description": "Maximum number of sentences per chunk",
                "default": 10,
                "min": 1
            },
            "max_chunk_size": {
                "type": "int",
                "description": "Maximum chunk size in characters (overrides sentence limit)",
                "default": 2000,
                "min": 100
            }
        }
    
    async def chunk_text(
        self, 
        text: str, 
        chunk_size: int = 1000,  # Not used, kept for interface compatibility
        overlap: int = 200,      # Not used for sentence-based chunking
        **kwargs
    ) -> List[DocumentChunk]:
        max_sentences = kwargs.get('max_sentences', self.config.parameters.get('max_sentences', 10))
        max_chunk_size = kwargs.get('max_chunk_size', self.config.parameters.get('max_chunk_size', 2000))
        
        # Simple sentence splitting (could be enhanced with NLP libraries)
        sentence_pattern = r'[.!?]+\s+'
        sentences = re.split(sentence_pattern, text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_index = 0
        sentence_start = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if adding this sentence would exceed limits
            would_exceed_sentences = len(current_chunk) >= max_sentences
            would_exceed_size = current_length + len(sentence) > max_chunk_size
            
            if (would_exceed_sentences or would_exceed_size) and current_chunk:
                # Create chunk with current sentences
                chunk_content = '. '.join(current_chunk)
                if not chunk_content.endswith('.'):
                    chunk_content += '.'
                
                chunk = DocumentChunk(
                    chunk_id=f"chunk_{chunk_index}_{uuid.uuid4().hex[:8]}",
                    document_id="",
                    content=chunk_content,
                    start_pos=sentence_start,
                    end_pos=sentence_start + len(chunk_content),
                    metadata={
                        "chunk_index": chunk_index,
                        "chunk_method": "sentence_based",
                        "sentence_count": len(current_chunk)
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # Start new chunk
                current_chunk = []
                current_length = 0
                sentence_start += len(chunk_content)
            
            current_chunk.append(sentence)
            current_length += len(sentence)
        
        # Add remaining sentences as final chunk
        if current_chunk:
            chunk_content = '. '.join(current_chunk)
            if not chunk_content.endswith('.'):
                chunk_content += '.'
            
            chunk = DocumentChunk(
                chunk_id=f"chunk_{chunk_index}_{uuid.uuid4().hex[:8]}",
                document_id="",
                content=chunk_content,
                start_pos=sentence_start,
                end_pos=sentence_start + len(chunk_content),
                metadata={
                    "chunk_index": chunk_index,
                    "chunk_method": "sentence_based",
                    "sentence_count": len(current_chunk)
                }
            )
            chunks.append(chunk)
        
        return chunks


class SimpleNERProcessor(BaseNERProcessor):
    """
    Simple regex-based Named Entity Recognition processor.
    This is a basic implementation for demonstration - production systems
    would use more sophisticated NLP models like spaCy or Transformers.
    """
    
    def __init__(self, config: ProcessorConfig = None):
        if config is None:
            config = ProcessorConfig(
                processor_id="simple_ner",
                processing_type=ProcessingType.NER,
                name="Simple NER Processor",
                description="Basic regex-based named entity recognition",
                parameters={
                    "entity_types": ["PERSON", "EMAIL", "PHONE", "URL"]
                }
            )
        super().__init__(config)
    
    def get_supported_formats(self) -> List[DocumentFormat]:
        return [
            DocumentFormat.TEXT,
            DocumentFormat.MARKDOWN,
            DocumentFormat.HTML
        ]
    
    def get_required_parameters(self) -> Dict[str, Any]:
        return {}
    
    def get_optional_parameters(self) -> Dict[str, Any]:
        return {
            "entity_types": {
                "type": "list",
                "description": "List of entity types to extract",
                "default": ["PERSON", "EMAIL", "PHONE", "URL"],
                "options": ["PERSON", "EMAIL", "PHONE", "URL", "DATE", "NUMBER"]
            },
            "confidence_threshold": {
                "type": "float",
                "description": "Minimum confidence score for entities",
                "default": 0.5,
                "min": 0.0,
                "max": 1.0
            }
        }
    
    async def extract_entities(
        self, 
        text: str,
        entity_types: Optional[List[str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        if entity_types is None:
            entity_types = self.config.parameters.get('entity_types', ["PERSON", "EMAIL", "PHONE", "URL"])
        
        confidence_threshold = kwargs.get('confidence_threshold', 0.5)
        entities = []
        
        # Define regex patterns for different entity types
        patterns = {
            "EMAIL": (
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                0.9  # High confidence for email regex
            ),
            "PHONE": (
                r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
                0.8
            ),
            "URL": (
                r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?',
                0.9
            ),
            "DATE": (
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b',
                0.7
            ),
            "NUMBER": (
                r'\b\d+(?:\.\d+)?\b',
                0.6
            ),
            "PERSON": (
                r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Simple: First Last
                0.4  # Lower confidence for simple name pattern
            )
        }
        
        for entity_type in entity_types:
            if entity_type in patterns:
                pattern, base_confidence = patterns[entity_type]
                
                for match in re.finditer(pattern, text):
                    if base_confidence >= confidence_threshold:
                        entities.append({
                            "type": entity_type,
                            "text": match.group(),
                            "start": match.start(),
                            "end": match.end(),
                            "confidence": base_confidence,
                            "method": "regex"
                        })
        
        # Sort entities by position in text
        entities.sort(key=lambda x: x["start"])
        
        return entities


class MetadataExtractor(BaseDocumentProcessor):
    """
    Processor that extracts metadata from documents.
    """
    
    def __init__(self, config: ProcessorConfig = None):
        if config is None:
            config = ProcessorConfig(
                processor_id="metadata_extractor",
                processing_type=ProcessingType.METADATA_EXTRACTION,
                name="Metadata Extractor",
                description="Extracts basic metadata from document content",
                parameters={}
            )
        super().__init__(config)
    
    def get_supported_formats(self) -> List[DocumentFormat]:
        return [fmt for fmt in DocumentFormat]  # Support all formats
    
    def get_required_parameters(self) -> Dict[str, Any]:
        return {}
    
    def get_optional_parameters(self) -> Dict[str, Any]:
        return {
            "extract_stats": {
                "type": "bool",
                "description": "Whether to extract text statistics",
                "default": True
            },
            "detect_language": {
                "type": "bool",
                "description": "Whether to attempt language detection",
                "default": False
            }
        }
    
    async def process(
        self, 
        document: ProcessedDocument, 
        context: ProcessingContext,
        **kwargs
    ) -> ProcessingResult:
        start_time = datetime.utcnow()
        
        try:
            extract_stats = kwargs.get('extract_stats', True)
            detect_language = kwargs.get('detect_language', False)
            
            text_content = document.processed_content or document.raw_content or ""
            metadata = {}
            
            if extract_stats:
                # Basic text statistics
                metadata.update({
                    "character_count": len(text_content),
                    "word_count": len(text_content.split()),
                    "line_count": text_content.count('\n') + 1,
                    "paragraph_count": len([p for p in text_content.split('\n\n') if p.strip()]),
                    "avg_word_length": sum(len(word) for word in text_content.split()) / max(len(text_content.split()), 1)
                })
            
            if detect_language:
                # Simple language detection (could be enhanced with proper libraries)
                # This is a placeholder - in practice, use libraries like langdetect
                common_english_words = {'the', 'and', 'is', 'in', 'to', 'of', 'a', 'that'}
                words = set(text_content.lower().split())
                english_score = len(words.intersection(common_english_words)) / max(len(words), 1)
                
                if english_score > 0.1:
                    metadata["detected_language"] = "en"
                    metadata["language_confidence"] = min(english_score * 5, 1.0)
                else:
                    metadata["detected_language"] = "unknown"
                    metadata["language_confidence"] = 0.0
            
            # Update document metadata
            document.metadata.update(metadata)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ProcessingResult(
                processor_id=self.processor_id,
                processing_type=self.processing_type,
                status=ProcessingStatus.COMPLETED,
                input_document_id=document.document_id,
                output_data=metadata,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            return ProcessingResult(
                processor_id=self.processor_id,
                processing_type=self.processing_type,
                status=ProcessingStatus.FAILED,
                input_document_id=document.document_id,
                error_message=str(e),
                processing_time=processing_time
            ) 